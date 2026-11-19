# Painel da agência na nuvem (VPS)

Hoje o painel roda no seu PC. Ele já está pronto para ir para uma VPS quando você quiser.
Na nuvem, três coisas passam a funcionar de qualquer lugar:

1. **Portal do cliente**: o link que você manda pelo WhatsApp abre no celular dele, em qualquer rede.
2. **Conectar o Instagram por link**: o cliente toca em "Conectar meu Instagram", faz login e autoriza. Você não precisa pedir senha nem token.
3. **Publicação dos clientes 24 h**: o agendador roda o tempo todo, sem depender do seu PC ligado.
   Carrossel e foto dos clientes também passam a publicar, porque o painel serve as imagens por HTTPS.

O @projectatech continua sendo publicado pelo GitHub Actions, como hoje.

## O que você precisa
- Uma VPS Linux pequena (1 vCPU, 1 GB de RAM basta) com Docker. Ex.: Hostinger VPS, DigitalOcean, Hetzner.
- Um subdomínio apontando para o IP da VPS (registro A), ex.: `painel.projectatech.com.br`.
- Um app da Meta com o produto **API do Instagram com login do Instagram** (pode ser o mesmo app da Projecta):
  - Em *Configurações do login de negócios do Instagram*, cadastre a URL de redirecionamento
    `https://SEU-DOMINIO/conectar/retorno` (exatamente assim).
  - Copie o **ID do app do Instagram** e a **chave secreta do app do Instagram**.
  - Enquanto o app estiver em modo de desenvolvimento, cada cliente precisa ser adicionado como
    *testador do Instagram* (Funções do app) e aceitar o convite no Instagram dele.
    Para liberar para qualquer cliente sem convite: verificação da empresa + Análise do app pedindo
    `instagram_business_basic`, `instagram_business_content_publish` e `instagram_business_manage_comments`.

## Subir
```bash
git clone https://github.com/LeonardoStuani/projecta-instagram.git && cd projecta-instagram
# copie do seu PC para a VPS (por scp, nunca pelo git): .env, a pasta clientes/ e a pasta segredos/
echo "META_APP_ID=..."     >> .env
echo "META_APP_SECRET=..." >> .env
cd deploy && DOMINIO=painel.seudominio.com.br docker compose up -d --build
docker compose logs -f painel
```
No primeiro start, o painel cria `PAINEL_CHAVE` no `.env`. Seu acesso de agência é
`https://SEU-DOMINIO/?chave=<PAINEL_CHAVE>`: abra uma vez em cada aparelho (vira cookie) e não compartilhe.
Os links dos portais dos clientes mudam de endereço: reenvie a partir de *Conexões do cliente*.

## Segurança
- Na nuvem, todo acesso à agência exige a chave (inclusive "de dentro" do servidor).
- Cada cliente só enxerga o próprio portal. "Gerar link novo" invalida o anterior.
- Tokens dos clientes ficam em `segredos/<cliente>.env` na VPS. Faça backup cifrado dessa pasta.
- Tokens do login do Instagram valem 60 dias. O painel renova sozinho quando passam de 20 dias.

## Atualizar
```bash
git pull && cd deploy && docker compose restart painel
```

## Alternativa sem VPS
Rodar no PC de vocês (ou em um PC interno do cliente) com o atalho
"Abrir painel do Instagram (com celular)". O portal funciona só na mesma rede Wi-Fi, a conexão por link
não funciona, e o cliente precisa ser conectado colando o token em *Conexões*.
