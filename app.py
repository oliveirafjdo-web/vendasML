from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import csv
import io
from datetime import datetime

import pandas as pd

from database import get_connection, init_db

app = Flask(__name__)
app.secret_key = "redutron-secret-key"

init_db()


@app.route("/")
def index():
    return render_template("index.html")


# ------- PRODUTOS -------

@app.route("/produtos")
def listar_produtos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY name")
    products = cur.fetchall()
    conn.close()
    return render_template("products.html", products=products)


@app.route("/produtos/novo", methods=["POST"])
def criar_produto():
    try:
        name = request.form["name"].strip()
        sku = request.form.get("sku") or None
        variable_cost = float(request.form["variable_cost"])
        default_price = float(request.form["default_price"])
    except Exception:
        flash("Erro ao ler dados do produto. Confira os campos.", "error")
        return redirect(url_for("listar_produtos"))

    if not name:
        flash("Nome do produto é obrigatório.", "error")
        return redirect(url_for("listar_produtos"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (name, sku, variable_cost, default_price) VALUES (?, ?, ?, ?)",
        (name, sku, variable_cost, default_price),
    )
    conn.commit()
    conn.close()

    flash("Produto cadastrado com sucesso!", "success")
    return redirect(url_for("listar_produtos"))


# ------- VENDAS -------

@app.route("/vendas")
def listar_vendas():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT s.id, s.date, s.quantity, s.unit_price,
               s.marketplace_fee, s.shipping_cost, s.other_variable_cost, s.discount,
               p.name AS product_name
        FROM sales s
        JOIN products p ON p.id = s.product_id
        ORDER BY s.date DESC, s.id DESC
        """
    )
    sales = cur.fetchall()

    cur.execute("SELECT id, name FROM products ORDER BY name")
    products = cur.fetchall()
    conn.close()

    return render_template("sales.html", sales=sales, products=products)


@app.route("/vendas/novo", methods=["POST"])
def criar_venda():
    try:
        product_id = int(request.form["product_id"])
        date = request.form["date"]
        quantity = float(request.form["quantity"])
        unit_price = float(request.form["unit_price"] or 0)
        marketplace_fee = float(request.form.get("marketplace_fee") or 0)
        shipping_cost = float(request.form.get("shipping_cost") or 0)
        other_variable_cost = float(request.form.get("other_variable_cost") or 0)
        discount = float(request.form.get("discount") or 0)
    except Exception:
        flash("Erro ao ler dados da venda. Confira os campos.", "error")
        return redirect(url_for("listar_vendas"))

    if quantity <= 0:
        flash("Quantidade deve ser maior que zero.", "error")
        return redirect(url_for("listar_vendas"))

    if not date:
        flash("Data é obrigatória.", "error")
        return redirect(url_for("listar_vendas"))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO sales (
            product_id, date, quantity, unit_price,
            marketplace_fee, shipping_cost, other_variable_cost, discount
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            product_id,
            date,
            quantity,
            unit_price,
            marketplace_fee,
            shipping_cost,
            other_variable_cost,
            discount,
        ),
    )
    conn.commit()
    conn.close()

    flash("Venda lançada com sucesso!", "success")
    return redirect(url_for("listar_vendas"))


# ------- RELATÓRIO / MARGEM / CURVA A -------

def calcular_relatorio(inicio, fim, criterio="faturamento"):
    conn = get_connection()
    cur = conn.cursor()

    params = []
    where = ""
    if inicio:
        where += " AND s.date >= ?"
        params.append(inicio)
    if fim:
        where += " AND s.date <= ?"
        params.append(fim)

    query = """
        SELECT
            p.id AS product_id,
            p.name AS product_name,
            SUM(s.quantity) AS total_qty,
            SUM(s.quantity * s.unit_price) AS faturamento_bruto,
            SUM(s.discount) AS total_desconto,
            SUM(s.quantity * p.variable_cost) AS custo_produto,
            SUM(s.marketplace_fee) AS total_marketplace_fee,
            SUM(s.shipping_cost) AS total_shipping_cost,
            SUM(s.other_variable_cost) AS total_other_cost
        FROM sales s
        JOIN products p ON p.id = s.product_id
        WHERE 1=1 {where}
        GROUP BY p.id, p.name
    """.format(where=where)

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    relatorio = []
    total_faturamento_liquido_geral = 0.0

    for r in rows:
        faturamento_bruto = r["faturamento_bruto"] or 0
        total_desconto = r["total_desconto"] or 0
        faturamento_liquido = faturamento_bruto - total_desconto

        custo_produto = r["custo_produto"] or 0
        total_marketplace_fee = r["total_marketplace_fee"] or 0
        total_shipping_cost = r["total_shipping_cost"] or 0
        total_other_cost = r["total_other_cost"] or 0

        total_custos_variaveis = (
            custo_produto + total_marketplace_fee + total_shipping_cost + total_other_cost
        )

        margem_contrib = faturamento_liquido - total_custos_variaveis
        margem_pct = (margem_contrib / faturamento_liquido * 100) if faturamento_liquido > 0 else 0

        relatorio.append(
            {
                "product_id": r["product_id"],
                "product_name": r["product_name"],
                "total_qty": r["total_qty"] or 0,
                "faturamento_bruto": faturamento_bruto,
                "total_desconto": total_desconto,
                "faturamento_liquido": faturamento_liquido,
                "custo_produto": custo_produto,
                "total_marketplace_fee": total_marketplace_fee,
                "total_shipping_cost": total_shipping_cost,
                "total_other_cost": total_other_cost,
                "total_custos_variaveis": total_custos_variaveis,
                "margem_contrib": margem_contrib,
                "margem_pct": margem_pct,
            }
        )

        total_faturamento_liquido_geral += faturamento_liquido

    if total_faturamento_liquido_geral == 0:
        return [], 0, 0

    if criterio == "margem":
        key_fn = lambda x: x["margem_contrib"]
    else:
        key_fn = lambda x: x["faturamento_liquido"]

    relatorio.sort(key=key_fn, reverse=True)

    cumulativo = 0.0
    for item in relatorio:
        base = item["faturamento_liquido"]
        cumulativo += base
        perc_acumulado = cumulativo / total_faturamento_liquido_geral * 100

        if perc_acumulado <= 80:
            curva = "A"
        elif perc_acumulado <= 95:
            curva = "B"
        else:
            curva = "C"

        item["perc_acumulado"] = perc_acumulado
        item["curva"] = curva

    return relatorio, total_faturamento_liquido_geral, len(relatorio)


@app.route("/relatorio", methods=["GET", "POST"])
def relatorio():
    inicio = fim = None
    criterio = "faturamento"

    if request.method == "POST":
        inicio = request.form.get("inicio") or None
        fim = request.form.get("fim") or None
        criterio = request.form.get("criterio") or "faturamento"

    dados, total_fat_liq, total_itens = calcular_relatorio(inicio, fim, criterio)

    return render_template(
        "report.html",
        dados=dados,
        total_fat_liq=total_fat_liq,
        total_itens=total_itens,
        inicio=inicio,
        fim=fim,
        criterio=criterio,
    )


@app.route("/relatorio/csv")
def relatorio_csv():
    inicio = request.args.get("inicio") or None
    fim = request.args.get("fim") or None
    criterio = request.args.get("criterio") or "faturamento"

    dados, total_fat_liq, _ = calcular_relatorio(inicio, fim, criterio)

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(
        [
            "Produto",
            "Quantidade",
            "Faturamento bruto",
            "Descontos",
            "Faturamento líquido",
            "Custo produto",
            "Comissão marketplace",
            "Frete",
            "Outros custos",
            "Custos variáveis totais",
            "Margem contribuição (R$)",
            "Margem (%)",
            "Curva",
        ]
    )

    for d in dados:
        writer.writerow(
            [
                d["product_name"],
                d["total_qty"],
                f"{d['faturamento_bruto']:.2f}",
                f"{d['total_desconto']:.2f}",
                f"{d['faturamento_liquido']:.2f}",
                f"{d['custo_produto']:.2f}",
                f"{d['total_marketplace_fee']:.2f}",
                f"{d['total_shipping_cost']:.2f}",
                f"{d['total_other_cost']:.2f}",
                f"{d['total_custos_variaveis']:.2f}",
                f"{d['margem_contrib']:.2f}",
                f"{d['margem_pct']:.2f}",
                d["curva"],
            ]
        )

    writer.writerow([])
    writer.writerow(["TOTAL FATURAMENTO LÍQUIDO", f"{total_fat_liq:.2f}"])

    output.seek(0)
    filename = "relatorio_vendas_v3.csv"

    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename,
    )


# ------- IMPORTAÇÃO XLSX MERCADO LIVRE -------

MESES_PT = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


def to_float(value):
    if value is None:
        return 0.0
    try:
        if isinstance(value, str):
            v = value.strip().replace("R$", "").replace(" ", "")
            v = v.replace(".", "").replace(",", ".")
            return float(v) if v else 0.0
        if pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def parse_data_ml(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    v = str(value).strip()
    parts = v.split()
    try:
        dia = int(parts[0])
        mes_nome = parts[2].lower()
        ano = int(parts[4])
        mes = MESES_PT.get(mes_nome)
        if not mes:
            return None
        dt = datetime(ano, mes, dia)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


@app.route("/importar", methods=["GET", "POST"])
def importar_vendas():
    if request.method == "GET":
        return render_template("import.html")

    arquivo = request.files.get("arquivo")
    if not arquivo or arquivo.filename == "":
        flash("Nenhum arquivo selecionado.", "error")
        return redirect(url_for("importar_vendas"))

    try:
        df = pd.read_excel(arquivo, header=5)
    except Exception as e:
        flash(f"Erro ao ler o arquivo XLSX: {e}", "error")
        return redirect(url_for("importar_vendas"))

    col_sku = "SKU"
    col_data = "Data da venda"
    col_unidades = "Unidades"
    col_preco_unit = "Preço unitário de venda do anúncio (BRL)"
    col_taxa_venda = "Tarifa de venda e impostos (BRL)"

    registros = df.to_dict(orient="records")

    conn = get_connection()
    cur = conn.cursor()

    importados = 0
    erros = 0

    for row in registros:
        try:
            sku = str(row.get(col_sku) or "").strip()
            if not sku:
                erros += 1
                continue

            data_ml = row.get(col_data)
            data = parse_data_ml(data_ml)
            if not data:
                erros += 1
                continue

            quantidade = to_float(row.get(col_unidades) or 1)
            if quantidade <= 0:
                erros += 1
                continue

            preco_unitario = to_float(row.get(col_preco_unit) or 0)

            taxa_venda = to_float(row.get(col_taxa_venda) or 0)
            marketplace_fee = abs(taxa_venda)

            shipping_cost = 0.0
            other_cost = 0.0
            discount = 0.0

            cur.execute("SELECT id FROM products WHERE sku = ?", (sku,))
            prod = cur.fetchone()

            if prod:
                product_id = prod["id"]
            else:
                nome_prod = sku
                variable_cost = 0.0
                default_price = preco_unitario
                cur.execute(
                    "INSERT INTO products (name, sku, variable_cost, default_price) VALUES (?, ?, ?, ?)",
                    (nome_prod, sku, variable_cost, default_price),
                )
                product_id = cur.lastrowid

            cur.execute(
                """
                INSERT INTO sales (
                    product_id, date, quantity, unit_price,
                    marketplace_fee, shipping_cost, other_variable_cost, discount
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product_id,
                    data,
                    quantidade,
                    preco_unitario,
                    marketplace_fee,
                    shipping_cost,
                    other_cost,
                    discount,
                ),
            )
            importados += 1
        except Exception:
            erros += 1
            continue

    conn.commit()
    conn.close()

    if importados:
        flash(
            f"Importação concluída. Vendas importadas: {importados}. Linhas com erro: {erros}.",
            "success",
        )
    else:
        flash("Nenhuma venda foi importada. Verifique o arquivo.", "error")

    return redirect(url_for("listar_vendas"))


if __name__ == "__main__":
    app.run(debug=True)
