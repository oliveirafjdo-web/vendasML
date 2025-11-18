# Controle de Vendas Redutron v2

Versão 2.0 do sistema de controle de vendas, com:

- Cálculo de **faturamento bruto** e **líquido** (considerando descontos).
- Controle de **custos variáveis detalhados**:
  - Comissão de marketplace (ex.: Mercado Livre, Shopee)
  - Frete pago por você
  - Outros custos variáveis (embalagem, taxas, etc.)
- Cálculo de **margem de contribuição** em valor e em %.
- Classificação **Curva ABC**:
  - A = até 80% do faturamento líquido acumulado
  - B = de 80% a 95%
  - C = acima de 95%
- Exportação de relatório em CSV.
- Layout com identidade inspirada na marca **Redutron**.

## Como funciona a lógica financeira

Para cada produto no relatório:

- **Faturamento bruto** = soma de `quantidade × preço de venda`.
- **Descontos** = soma de todos os descontos concedidos.
- **Faturamento líquido** = `Faturamento bruto − Descontos`.
- **Custo do produto** = `quantidade × custo variável unitário` (cadastrado no produto).
- **Comissão marketplace** = soma das comissões informadas por venda.
- **Frete** = soma do frete que saiu do seu bolso.
- **Outros custos** = embalagem, taxas, etc.
- **Custos variáveis totais** = `Custo produto + Comissão + Frete + Outros`.
- **Margem de contribuição (R$)** = `Faturamento líquido − Custos variáveis totais`.
- **Margem (%)** = `Margem de contribuição ÷ Faturamento líquido × 100`.

## Curva ABC

Os produtos são ordenados pelo critério escolhido:

- **Faturamento líquido** (padrão), ou
- **Margem de contribuição total**.

Em seguida, calculamos o faturamento líquido acumulado e classificamos:

- **Curva A**: até 80% do faturamento acumulado.
- **Curva B**: de 80% a 95%.
- **Curva C**: acima de 95%.

Isso ajuda você a focar nos produtos que mais trazem resultado.

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

> Se você já usou a versão 1.0, o sistema tenta adicionar as novas colunas na tabela `sales`
> sem apagar as vendas antigas.

## Estrutura de pastas

```text
controle-vendas-redutron-v2/
├─ app.py
├─ database.py
├─ requirements.txt
├─ README.md
├─ /templates
│  ├─ base.html
│  ├─ index.html
│  ├─ products.html
│  ├─ sales.html
│  └─ report.html
└─ /static
   └─ style.css
```

## Como publicar no GitHub (passo a passo)

1. Crie um repositório vazio no GitHub, por exemplo com o nome:

   **controle-vendas-redutron-v2**

   Sem adicionar README, `.gitignore` ou licença (deixa tudo vazio).

2. No seu computador, extraia o ZIP deste projeto em uma pasta, por exemplo:

   `C:\Projetos\controle-vendas-redutron-v2` (Windows)  
   ou  
   `~/projetos/controle-vendas-redutron-v2` (Linux/macOS)

3. Abra o terminal (ou Prompt de Comando/PowerShell) dentro dessa pasta:

```bash
cd caminho/para/controle-vendas-redutron-v2
```

4. Inicialize o repositório Git e faça o primeiro commit:

```bash
git init
git add .
git commit -m "Versão 2.0 - controle de vendas Redutron"
```

5. Conecte o repositório local ao GitHub (substitua `SEU_USUARIO`):

```bash
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/controle-vendas-redutron-v2.git
```

6. Envie os arquivos para o GitHub:

```bash
git push -u origin main
```

Pronto! Seu sistema de controle de vendas Redutron v2 estará publicado e pronto para ser mostrado para clientes, parceiros ou mentoria de e-commerce.
