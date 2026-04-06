from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q
from .models import Material
import openpyxl
from django.db.models import Sum, F, Count
from django.utils.timezone import make_aware
from datetime import datetime
import json
from django.contrib.auth.decorators import login_required
import pandas as pd
from django.contrib import messages

# No topo do seu views.py


TABELA_DE_PRECOS = {
    '300092': 12.50,  # Manta térmica
    '300752': 45.00,  # Telha metálica galvanizada
    '319013': 38.90,  # Cimento 50kg
    '320426': 95.00,  # Areia média
    '322223': 110.00, # Brita nº1
    '300768': 2.50,   # Cal hidratada
    '314003': 1.10,   # Tijolo baiano
    '300767': 18.00,  # Canaleta de concreto
}
def editar_material(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == "POST":
        # Aqui capturamos os novos dados do formulário
        material.Quantidade = request.POST.get('quantidade')
        material.Preco_Unitario = request.POST.get('preco').replace(',', '.')
        material.save()
        return redirect('home')
    return render(request, 'materiais/editar.html', {'material': material})

# VIEW PARA EXCLUIR
def excluir_material(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == "POST":
        material.delete()
    return redirect('home')

# 1. ESTA SERÁ A SUA NOVA PÁGINA PRINCIPAL (O BUSCADOR)
def index(request):
    return render(request, 'materiais/index.html')

# 2. ESTA É A PÁGINA DE CADASTRO (ONDE OS MATERIAIS SÃO SALVOS)


def materiais_cadastrados(request):
    # 1. IDENTIFICAÇÃO DA OBRA
    numero_obra = request.GET.get('numero_obra') or request.POST.get('numero_obra')
    
    # 2. LÓGICA DE EDIÇÃO (CARREGAR DADOS)
    editar_id = request.GET.get('editar_id')
    material_editar = None
    if editar_id:
        material_editar = get_object_or_404(Material, id=editar_id)

    # 3. PROCESSAMENTO DO FORMULÁRIO (SALVAR/EDITAR)
    if request.method == 'POST':
        material_id = request.POST.get('material_id')
        codigo_digitado = request.POST.get('codigo')
        
        try:
            # Busca o preço no seu dicionário TABELA_DE_PRECOS (defina-o no topo do arquivo)
            preco_auto = TABELA_DE_PRECOS.get(codigo_digitado, 0.00)

            qtd_raw = request.POST.get('quantidade')
            lote_raw = request.POST.get('lote')

            if not all([codigo_digitado, qtd_raw, lote_raw]):
                messages.error(request, "Preencha todos os campos obrigatórios.")
                return redirect(f'/materiais-cadastrados/?numero_obra={numero_obra}')

            dados = {
                'Codigo': codigo_digitado,
                'Descricao': request.POST.get('descricao'),
                'Quantidade': int(qtd_raw),
                'Lote': lote_raw,
                'Obra': numero_obra,
                'Preco_Unitario': preco_auto 
            }

            if material_id: # ATUALIZAR EXISTENTE
                Material.objects.filter(id=material_id).update(**dados)
                messages.success(request, "Material atualizado com sucesso (Preço reajustado).")
            else: # CRIAR NOVO
                Material.objects.create(**dados)
                messages.success(request, "Material cadastrado com sucesso!")
            
            # O REDIRECT LIMPA OS DADOS DO POST E EVITA CADASTRO DUPLICADO AO ATUALIZAR A PÁGINA
            return redirect(f'/materiais-cadastrados/?numero_obra={numero_obra}')

        except ValueError:
            messages.error(request, "Erro nos dados: Verifique se a quantidade é um número válido.")
            return redirect(f'/materiais-cadastrados/?numero_obra={numero_obra}')

    # 4. FILTRO INTELIGENTE E BUSCA
    termo_busca = request.GET.get('busca', '').strip()
    query = Q(Obra=numero_obra)
    
    if termo_busca:
        query &= (
            Q(Descricao__icontains=termo_busca) | 
            Q(Codigo__icontains=termo_busca) | 
            Q(Lote__icontains=termo_busca)
        )

    materiais_da_obra = Material.objects.filter(query).order_by('-data_criacao')
    
    # 5. RENDERIZAÇÃO DO CONTEXTO
    contexto = {
        'materiais': materiais_da_obra,
        'numero_obra': numero_obra,
        'material_editar': material_editar,
        # Não é mais necessário passar as mensagens manualmente aqui
    }
    return render(request, 'materiais/materiais_cadastrados.html', contexto)

@login_required
def home(request):
    # 1. CAPTURA OS FILTROS DE DATA
    data_inicio = request.GET.get('data_inicio')
    data_fim = request.GET.get('data_fim')
    
    # 2. BUSCA BASE DE MATERIAIS (Ordenados pelos mais recentes)
    materiais = Material.objects.all().order_by('-data_criacao')

    # 3. APLICA OS FILTROS SE EXISTIREM
    if data_inicio:
        materiais = materiais.filter(data_criacao__date__gte=data_inicio)
    if data_fim:
        materiais = materiais.filter(data_criacao__date__lte=data_fim)

    # 4. LÓGICA DE EXPORTAÇÃO PARA EXCEL (PANDAS)
    if request.GET.get('exportar') == 'excel':
        data = []
        for m in materiais:
            data.append({
                'Código': m.Codigo,
                'Descrição': m.Descricao,
                'Quantidade': m.Quantidade,
                'Lote': m.Lote,
                'Preço Unitário': m.Preco_Unitario,
                'Subtotal': m.Quantidade * m.Preco_Unitario,
                'Obra': m.Obra,
                'Data de Cadastro': m.data_criacao.strftime('%d/%m/%Y %H:%M')
            })
        
        df = pd.DataFrame(data)
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=Relatorio_Producao_Filtrado.xlsx'
        
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Materiais')
        
        return response

    # 5. CÁLCULOS PARA O DASHBOARD (VALOR TOTAL)
    # Calculamos o subtotal de cada item e somamos tudo
    valor_total = materiais.annotate(
        subtotal=F('Quantidade') * F('Preco_Unitario')
    ).aggregate(total_geral=Sum('subtotal'))['total_geral'] or 0

    # 6. DADOS PARA O GRÁFICO DE BARRAS (INVESTIMENTO POR OBRA)
    investimento_por_obra = materiais.values('Obra').annotate(
        total=Sum(F('Quantidade') * F('Preco_Unitario'))
    ).order_by('-total')

    labels_grafico = [item['Obra'] if item['Obra'] else "Sem Obra" for item in investimento_por_obra]
    valores_grafico = [float(item['total']) for item in investimento_por_obra]

    # 7. A PROPRIEDADE total_item DO MODELO JÁ FORNECE O CÁLCULO CORRETO

    context = {
        'materiais': materiais,
        'valor_total': valor_total,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'labels_grafico': labels_grafico,
        'valores_grafico': valores_grafico,
    }

    return render(request, 'materiais/home.html', context)

def exportar_excel(request, numero_obra):
    # Cria um novo arquivo Excel na memória
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"Obra {numero_obra}"

    # Cabeçalho da planilha
    colunas = ['Código', 'Descrição', 'Quantidade', 'Lote', 'Data de Cadastro']
    ws.append(colunas)

    # Busca os materiais específicos desta obra
    materiais = Material.objects.filter(Obra=numero_obra)

    for material in materiais:
        ws.append([
            material.Codigo,
            material.Descricao,
            material.Quantidade,
            material.Lote,
            material.data_criacao.strftime('%d/%m/%Y %H:%M')
        ])

    # Prepara a resposta do navegador para download
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="Relatorio_Obra_{numero_obra}.xlsx"'
    
    wb.save(response)
    return response

def lista_obras(request):
    # Agrupa por 'Obra', conta os itens e soma o valor total de cada uma
    obras_resumo = Material.objects.values('Obra').annotate(
        total_itens=Count('id'),
        valor_total_obra=Sum(F('Quantidade') * F('Preco_Unitario'))
    ).order_by('Obra')

    return render(request, 'materiais/lista_obras.html', {'obras': obras_resumo})


