import asyncio
import os
import sys
from playwright.async_api import async_playwright
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

async def capture_screenshot():
    print("Capturando screenshot da aplicação...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()
        try:
            await page.goto("http://localhost:30080", timeout=10000)
            await page.wait_for_timeout(3000)
            
            # Start game to show active state
            await page.click("text=Começar Novo Jogo")
            await page.wait_for_timeout(1000)
            
            # Make a guess to show attempts and feedback
            await page.fill("input[placeholder='Seu palpite']", "50")
            await page.click("text=Palpitar")
            await page.wait_for_timeout(1500)
            
            await page.screenshot(path="game_screenshot.png")
            print("Screenshot capturado com sucesso como game_screenshot.png")
        except Exception as e:
            print(f"Erro ao capturar screenshot: {e}")
            # Create a dummy image if playwright fails
            from PIL import Image as PILImage, ImageDraw
            img = PILImage.new('RGB', (800, 500), color='#1e1e1e')
            draw = ImageDraw.Draw(img)
            draw.text((100, 200), "Erro na captura do jogo rodando no NodePort 30080", fill="white")
            img.save("game_screenshot.png")
        finally:
            await browser.close()

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        # Do not draw on cover page (Page 1)
        if self._pageNumber == 1:
            return
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#4b5563"))
        
        # Header
        self.drawString(54, 750, "Relatório Técnico: Guessing Game no Kubernetes")
        self.setStrokeColor(colors.HexColor("#e5e7eb"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        
        # Footer
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(558, 40, page_text)
        self.drawString(54, 40, "Unidade 1 - Orquestração de Containers")
        self.line(54, 52, 558, 52)
        
        self.restoreState()

def create_pdf(filename="Relatorio_Kubernetes_GuessGame.pdf"):
    print("Gerando PDF do Relatório Técnico...")
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()
    
    # Custom Styles
    primary_color = colors.HexColor("#1e3a8a") # Dark Blue
    secondary_color = colors.HexColor("#0f766e") # Teal
    text_dark = colors.HexColor("#1f2937")
    
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=15,
        alignment=1 # Centered
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=14,
        leading=18,
        textColor=secondary_color,
        spaceAfter=30,
        alignment=1 # Centered
    )
    
    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_dark,
        spaceAfter=10,
        alignment=1
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=primary_color,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=secondary_color,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyText_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_dark,
        spaceAfter=8,
        alignment=4 # Justified
    )
    
    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#111827"),
        backColor=colors.HexColor("#f3f4f6"),
        borderColor=colors.HexColor("#e5e7eb"),
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=10
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_dark,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    story = []

    # ================= COVER PAGE =================
    story.append(Spacer(1, 100))
    story.append(Paragraph("UNIVERSIDADE DO ALUNO", title_style))
    story.append(Paragraph("Curso de Especialização em Arquitetura de Software & DevOps", subtitle_style))
    story.append(Spacer(1, 40))
    
    # Title Block
    title_box_data = [
        [Paragraph("<font size=20 color='#ffffff'><b>TRABALHO PRÁTICO – UNIDADE 1</b></font><br/><br/>"
                   "<font size=14 color='#e2e8f0'>Orquestração e Implantação Local de Microserviços no Kubernetes com k3d e Helm</font>", 
                   ParagraphStyle('TitleBox', parent=styles['Normal'], alignment=1))]
    ]
    title_box_table = Table(title_box_data, colWidths=[500])
    title_box_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), primary_color),
        ('PADDING', (0,0), (-1,-1), 20),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 25),
        ('TOPPADDING', (0,0), (-1,-1), 25),
    ]))
    story.append(title_box_table)
    story.append(Spacer(1, 100))
    
    # Meta Block
    story.append(Paragraph("<b>Estudante:</b> Guilherme Steinke", meta_style))
    story.append(Paragraph("<b>Disciplina:</b> Orquestração de Containers & Kubernetes", meta_style))
    story.append(Paragraph("<b>Professor:</b> IEC Professor", meta_style))
    story.append(Paragraph("<b>Data:</b> Julho de 2026", meta_style))
    story.append(PageBreak())

    # ================= PAGE 2: INTRO & DESIGN =================
    story.append(Paragraph("1. Introdução e Arquitetura do Sistema", h1_style))
    story.append(Paragraph(
        "Este relatório apresenta a migração e orquestração do jogo demonstrativo <i>Guess Game</i> "
        "para o ambiente de orquestração de containers <b>Kubernetes</b>, utilizando ferramentas do ecossistema "
        "cloud-native como <b>k3d</b> (cluster K3s local baseado em Docker) e <b>Helm</b> como gerenciador de pacotes.",
        body_style
    ))
    story.append(Paragraph(
        "A arquitetura original do projeto baseada em Docker Compose foi reestruturada para seguir os padrões declarativos "
        "e resilientes do Kubernetes, dividida em três componentes principais altamente coesos e fracamente acoplados:",
        body_style
    ))
    
    components_data = [
        ["Componente", "Função do Serviço", "Recursos Kubernetes Utilizados"],
        ["Database", "Banco de dados relacional Postgres para armazenar o histórico de palpites.", "Deployment, ClusterIP Service, PVC (Dynamic Path), Secret"],
        ["Backend", "API REST Flask (Python 3.12) executando lógica de negócio de adivinhação.", "Deployment, ClusterIP Service, HPA (Horizontal Pod Autoscaler)"],
        ["Frontend", "Cliente React servido por NGINX, que atua como proxy reverso para o backend.", "Deployment, NodePort Service, ConfigMap (Nginx Routing)"]
    ]
    components_table = Table(components_data, colWidths=[90, 210, 200])
    components_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f3f4f6")),
        ('TEXTCOLOR', (0,0), (-1,0), primary_color),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#d1d5db")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(components_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("2. Considerações de Design Críticas (Dia 0)", h1_style))
    
    story.append(Paragraph("2.1. Rede (Networking)", h2_style))
    story.append(Paragraph(
        "No Kubernetes, a comunicação entre Pods é baseada no modelo <i>IP-per-Pod</i>, gerenciada pelo Container Network Interface (CNI), "
        "que no k3d é o <b>Flannel</b>. Para isolar e estabilizar o tráfego interno:",
        body_style
    ))
    story.append(Paragraph("• <b>Service Discovery:</b> A comunicação interna backend-db e frontend-backend ocorre exclusivamente via DNS interno. O Service do banco de dados é nomeado <font face='Courier'>db</font> e o do Flask é <font face='Courier'>backend</font>, eliminando IPs fixos.", bullet_style))
    story.append(Paragraph("• <b>Nginx DNS Resolution:</b> A configuração original do Docker Compose utilizava a diretiva de resolução interna de DNS do Docker (<font face='Courier'>127.0.0.11</font>). No Kubernetes, isso causaria erro 502. Um ConfigMap foi implementado para montar a configuração correta do NGINX no container frontend, apontando a rota <font face='Courier'>/api/</font> diretamente para o Service ClusterIP <font face='Courier'>http://backend:5000</font>.", bullet_style))
    story.append(Paragraph("• <b>Exposição Externa:</b> Utilizou-se um serviço do tipo <b>NodePort</b> mapeado na porta estática <b>30080</b> no host local, eliminando a dependência obrigatória de Ingress Controllers em clusters de desenvolvimento.", bullet_style))

    story.append(Paragraph("2.2. Armazenamento (Storage)", h2_style))
    story.append(Paragraph(
        "A persistência dos dados do banco Postgres é garantida por meio de um <b>PersistentVolumeClaim (PVC)</b>. "
        "O Kubernetes local da distribuição K3s utiliza a StorageClass padrão <b>local-path</b>. "
        "Esse provisionador dinâmico aloca e monta diretórios do nó host de forma transparente, permitindo que os dados persistam "
        "mesmo após exclusões, reinicializações ou atualizações do Pod do banco de dados.",
        body_style
    ))
    story.append(PageBreak())

    # ================= PAGE 3: AUTO SCALE & DEPLOYMENT =================
    story.append(Paragraph("2.3. Disponibilidade e Escalabilidade (HPA)", h2_style))
    story.append(Paragraph(
        "A alta disponibilidade do backend Flask é controlada de forma dinâmica pelo recurso de <b>Horizontal Pod Autoscaler (HPA)</b>. "
        "Para que o HPA funcione no k3d, o componente <b>metrics-server</b> foi implantado no namespace kube-system com a flag "
        "<font face='Courier'>--kubelet-insecure-tls</font> para contornar problemas de certificados autoassinados em ambiente local.",
        body_style
    ))
    story.append(Paragraph(
        "Foram definidas as seguintes políticas de auto-scaling:",
        body_style
    ))
    story.append(Paragraph("• <b>Replicas Mínimas:</b> 2 Pods para garantir tolerância a falhas básicas.", bullet_style))
    story.append(Paragraph("• <b>Replicas Máximas:</b> 5 Pods para conter uso excessivo de recursos no nó.", bullet_style))
    story.append(Paragraph("• <b>Métrica Alvo:</b> 50% de uso de CPU do Pod.", bullet_style))
    story.append(Paragraph("• <b>Resource Requests/Limits:</b> Definidos como 100m CPU / 128Mi RAM (Request) e 200m CPU / 256Mi RAM (Limit) no backend. Sem limites definidos, o HPA fica inativo, pois não tem base percentual para cálculo de escala.", bullet_style))

    story.append(Paragraph("2.4. Gestão de Permissões (RBAC)", h2_style))
    story.append(Paragraph(
        "Em ambientes produtivos, a segurança é regida pelo <b>Role-Based Access Control (RBAC)</b>. "
        "A aplicação é executada sob a ServiceAccount padrão do namespace, sem privilégios extras adicionais de ClusterAdmin. "
        "Caso o backend precisasse consultar a API do Kubernetes, criaríamos uma <b>Role</b> restrita com verbos de leitura "
        "associada via <b>RoleBinding</b> à ServiceAccount específica do backend, seguindo o Princípio do Menor Privilégio.",
        body_style
    ))

    story.append(Paragraph("2.5. Facilidade de Implantação e Manutenibilidade", h2_style))
    story.append(Paragraph(
        "Utilizou-se o <b>Helm (Charts)</b> para estruturar a implantação como um pacote parametrizável. "
        "As definições de recursos, credenciais, imagens e portas foram centralizadas no arquivo <font face='Courier'>values.yaml</font>. "
        "Essa modularidade garante que a atualização das imagens (Dia 2) ocorra de forma simples e segura, utilizando o comando "
        "<font face='Courier'>helm upgrade</font> apenas alterando a tag da imagem no values.",
        body_style
    ))
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("3. Instalação e Implantação (Dia 1)", h1_style))
    story.append(Paragraph(
        "Para implantar a aplicação localmente no cluster k3d, execute o script automatizado <font face='Courier'>start_k8s.sh</font> "
        "na raiz do repositório. O fluxo do script executa as seguintes etapas:",
        body_style
    ))
    
    install_steps = [
        "1. Cria o cluster k3d mapeando a porta host 30080 para o NodePort do cluster.",
        "2. Copia e importa as imagens Docker locais do backend e frontend diretamente para os nós do k3d.",
        "3. Implanta e configura o Metrics Server com suporte a certificados insecure TLS.",
        "4. Instala o Helm Chart 'guess-game' no namespace default.",
        "5. Aguarda até que todos os componentes estejam totalmente prontos (Running/Ready)."
    ]
    for step in install_steps:
        story.append(Paragraph(step, bullet_style))
        
    story.append(Spacer(1, 10))
    story.append(Paragraph("Abaixo é exibido o screenshot do jogo rodando no navegador e integrado ao banco de dados via NodePort:", body_style))
    
    if os.path.exists("game_screenshot.png"):
        story.append(Image("game_screenshot.png", width=420, height=262))
    story.append(PageBreak())

    # ================= PAGE 4: OPERATION & CLOUD VS ONPREM =================
    story.append(Paragraph("4. Operação e Manutenção do Cluster (Dia 2)", h1_style))
    story.append(Paragraph(
        "A fase de manutenção contínua e suporte do Kubernetes foca em estabilidade operacional:",
        body_style
    ))
    story.append(Paragraph("• <b>Atualizações Zero-Downtime:</b> As atualizações de aplicação utilizam a estratégia padrão de <i>RollingUpdate</i>. "
                           "Novos pods são criados e passam por Probes de inicialização antes que os pods antigos sejam removidos.", bullet_style))
    story.append(Paragraph("• <b>Health Checks Proativos:</b> A API Flask possui um endpoint de saúde (<font face='Courier'>/api/health</font>) monitorado por <i>readinessProbe</i> "
                           "e <i>livenessProbe</i> que removem automaticamente pods lentos ou travados do balanceamento.", bullet_style))
    story.append(Paragraph("• <b>Políticas de Backup:</b> Para o banco Postgres local, o backup é feito via <font face='Courier'>pg_dump</font> direcionado ao volume NFS persistent "
                           "ou diretamente via CronJobs do Kubernetes executando tarefas agendadas de dump.", bullet_style))

    story.append(Paragraph("5. Comparativo: On-premises vs. Cloud Provider", h1_style))
    story.append(Paragraph(
        "Ao migrar de um ambiente local (k3d/on-premises) para uma nuvem pública (AWS EKS, GCP GKE, Azure AKS), "
        "várias camadas de infraestrutura mudam significativamente para alavancar os serviços gerenciados:",
        body_style
    ))
    
    compare_data = [
        ["Dimensão", "Ambiente On-premises / Local", "Nuvem Pública (EKS, GKE, AKS)"],
        ["Rede", "NodePort exposto em porta alta (ex: 30080). Balanceamento manual via NGINX.", "Integração nativa com Cloud Load Balancer (NLB/ALB) via Service Type: LoadBalancer."],
        ["Armazenamento", "Armazenamento local (local-path) preso aos nós. Risco alto de perda.", "Provisionamento dinâmico via CSI integrando volumes EBS, Azure Files ou EFS."],
        ["Disponibilidade", "Limitada pelo hardware dos nós físicos locais.", "Multi-AZ automático, autoscaling de nós (Cluster Autoscaler) e SLA do painel de controle."],
        ["Manutenção", "Administração completa do cluster, SO, rede e atualizações do K8s.", "Painel de controle gerenciado pelo provedor. Atualizações simplificadas de versão."]
    ]
    compare_table = Table(compare_data, colWidths=[90, 205, 205])
    compare_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f3f4f6")),
        ('TEXTCOLOR', (0,0), (-1,0), primary_color),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#d1d5db")),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(compare_table)

    story.append(Spacer(1, 15))
    story.append(Paragraph("6. Referências Bibliográficas", h1_style))
    story.append(Paragraph(
        "1. BURNS, Brendan; BEDA, Joe; HIGHTOWER, Kelsey. <i>Kubernetes: Up &amp; Running: Dive into the Future of Infrastructure</i>. 2. ed. Sebastopol: O'Reilly Media, 2019.",
        body_style
    ))
    story.append(Paragraph(
        "2. LUKSA, Marko. <i>Kubernetes in Action</i>. Shelter Island: Manning Publications, 2017.",
        body_style
    ))
    story.append(Paragraph(
        "3. HELM CONTRIBUTORS. <i>Helm Documentation</i>. Disponível em: &lt;https://helm.sh/docs/&gt;. Acesso em: 9 jul. 2026.",
        body_style
    ))
    story.append(Paragraph(
        "4. KUBERNETES AUTHORS. <i>Kubernetes Documentation</i>. Disponível em: &lt;https://kubernetes.io/docs/&gt;. Acesso em: 9 jul. 2026.",
        body_style
    ))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print("Relatório técnico PDF gerado com sucesso!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pdf-only":
        create_pdf()
    else:
        asyncio.run(capture_screenshot())
        create_pdf()
