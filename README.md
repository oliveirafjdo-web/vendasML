# Controle de Vendas Redutron v3 – com importação Mercado Livre

Versão 3.0 do sistema de controle de vendas, com:

- Cálculo de **faturamento bruto** e **líquido** (considerando descontos).
- Controle de **custos variáveis detalhados**:
  - Comissão de marketplace (Tarifa de venda e impostos do ML).
  - Frete, outros custos e desconto preenchidos manualmente se desejar.
- Cálculo de **margem de contribuição** em valor e em %.
- Classificação **Curva ABC**:
  - A = até 80% do faturamento líquido acumulado
  - B = de 80% a 95%
  - C = acima de 95%
- Exportação de relatório em CSV.
- **Importação direta** do relatório oficial de **Vendas BR** do Mercado Livre em XLSX.
- Layout com identidade inspirada na marca **Redutron**.

## Importação do Mercado Livre (XLSX)

Na aba **Importar**, você pode subir o arquivo XLSX de **Vendas BR** exatamente como o Mercado Livre fornece.

O sistema lê automaticamente as seguintes colunas:

- `SKU`
- `Data da venda`
- `Unidades`
- `Preço unitário de venda do anúncio (BRL)`
- `Tarifa de venda e impostos (BRL)`

Regras:

- `Tarifa de venda e impostos (BRL)` é usada como **comissão (`marketplace_fee`)**, sempre em valor positivo:
  - Exemplo: `-7,89` na planilha → `7,89` como custo de comissão.
- `shipping_cost`, `other_variable_cost` e `discount` são importados como `0` (você pode editar depois manualmente).

Para cada linha:

- Procura o produto pelo **SKU**.
- Se não existir, cria um produto automático com:
  - `name = SKU`
  - `variable_cost = 0`
  - `default_price = preço unitário do anúncio`
- Lança uma venda com:
  - Data convertida para `AAAA-MM-DD`.
  - Quantidade = `Unidades`.
  - Preço unitário = `Preço unitário de venda do anúncio (BRL)`.
  - Comissão (`marketplace_fee`) = valor absoluto de `Tarifa de venda e impostos (BRL)`.

## Como rodar localmente

1. Baixe este projeto (ZIP) e extraia em uma pasta, ou faça o clone do GitHub.

2. Dentro da pasta do projeto, crie e ative um ambiente virtual:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Execute o servidor:

```bash
python app.py
```

5. Acesse no navegador:

```
http://127.0.0.1:5000
```

O arquivo `vendas.db` será criado (ou atualizado) automaticamente na primeira execução.

## Deploy no Render

Este projeto já vem preparado para o Render:

- `requirements.txt` inclui `gunicorn`, `pandas` e `openpyxl`.
- `Procfile` contém:

  ```txt
  web: gunicorn app:app
  ```

No painel do Render, ao criar o Web Service:

- **Build Command:**

  ```bash
  pip install -r requirements.txt
  ```

- **Start Command:**

  ```bash
  gunicorn app:app
  ```

## Estrutura de pastas

```text
controle-vendas-redutron-v3-ml-import/
├─ app.py
├─ database.py
├─ requirements.txt
├─ Procfile
├─ README.md
├─ /templates
│  ├─ base.html
│  ├─ index.html
│  ├─ products.html
│  ├─ sales.html
│  ├─ report.html
│  └─ import.html
└─ /static
   └─ style.css
```

