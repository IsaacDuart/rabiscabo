# Mesa USB

Use um celular ou tablet **Android** como mesa digitalizadora para um **computador Linux**. A superfície abre no navegador do Android e envia os traços pelo cabo USB. No Linux, o receptor registra uma caneta virtual no sistema via `uinput`. Isso permite desenhar tanto em um programa nativo quanto em uma página web que aceite entrada de caneta. A pressão varia quando a caneta e o navegador do Android a fornecem. Com o dedo, ela é fixa.

## Preparar o Ubuntu

Você precisa de um cabo USB de dados, Python 3.10 ou posterior, [uv](https://docs.astral.sh/uv/getting-started/installation/), o ADB e acesso a `/dev/uinput`. O `uv` instala o pacote `evdev`, que usa um compilador e headers do Linux quando é instalado a partir do código-fonte. Instale as ferramentas do Ubuntu e execute na pasta do projeto:

```sh
sudo apt update
sudo apt install adb build-essential linux-libc-dev python3 python3-dev
uv sync --locked
```

Se `make run` reclamar de `/dev/uinput`, execute a configuração da sessão gráfica local com seu usuário normal. O `sudo` é usado para carregar o módulo `uinput` e instalar a regra de acesso do `udev`.

```sh
make setup
```

Se a permissão não aparecer após aplicar a regra, encerre a sessão gráfica e entre de novo. Após uma reinicialização, rode `make setup` novamente se o módulo ainda não estiver carregado.

## Conectar e desenhar

1. Ative as opções do desenvolvedor e a **Depuração USB** no Android. Conecte um único Android por cabo de dados e confirme a autorização na tela desbloqueada. Se `adb devices -l` mostrar `unauthorized`, confirme a mensagem no Android. Se mostrar falta de permissão no Linux, confira as regras USB do ADB da distribuição.
2. No Linux, execute o comando abaixo como seu usuário normal.

   ```sh
   make run
   ```

3. Mantenha a página **Mesa USB** visível no Android. Quando ela mostrar **Conectado por USB**, abra o aplicativo de desenho no Linux e toque na superfície no Android. Em uma página web de desenho, use um navegador com suporte a caneta no seu ambiente gráfico. Um pincel sensível à pressão permite testar a variação.
4. A área de desenho ocupa toda a página no Android, em pé ou deitado. A Mesa oculta a barra do navegador no primeiro toque. Se quiser voltar a esse modo depois de sair, toque em **Tela cheia**. Para ajustar a proporção da mesa virtual no Linux, execute, por exemplo, `uv run --locked -m src --proporcao 16:10`. Em sistemas com vários monitores, o ambiente gráfico determina o mapeamento da mesa.
5. Se desconectar o cabo, o receptor fica aguardando. Reconecte o mesmo Android e a página do Chrome será aberta novamente. Use **Ctrl+C** no computador para encerrar o receptor.

Deslize dois dedos juntos na superfície do Android para rolar na vertical ou na horizontal. A rolagem atua sob o cursor no computador e segue o comportamento de cada aplicativo.
Ative **Modo navegação** para rolar com um dedo, por exemplo em um feed. Toque novamente para voltar a desenhar.

Os traços enviados ficam visíveis na prévia do celular enquanto a página estiver aberta. Afaste dois dedos para aproximar e junte-os para afastar. Os botões **+** e **−** também ajustam o zoom. Toque em **Mover prévia** para arrastar o papel e toque novamente para voltar a desenhar. **Desfazer prévia** apaga a última marca no celular. O aplicativo no computador tem seu próprio zoom e histórico de ações.

Se o Chrome estiver instalado no Android, o receptor abre a página nele. Se a página não estabelecer a sessão, o terminal exibe o endereço completo após alguns segundos. Digite-o no Chrome do Android, incluindo o trecho após `#`, que contém a chave temporária.

## Conexão e segurança

A conexão fica em loopback nos dois aparelhos e atravessa o cabo por um túnel reverso do ADB. O servidor valida origem, chave aleatória por conexão USB, tamanho e conteúdo dos pacotes. Só uma aba ativa pode enviar traços. A caneta é liberada ao desconectar o cabo ou após cerca de 1,25 segundo sem resposta da página. A interface usa arquivos locais e roda offline.

A depuração USB concede ao computador autorizado acesso de desenvolvimento ao Android. Autorize apenas seu próprio computador e desative a opção quando terminar se não precisar dela para outra tarefa.

A versão atual suporta Android como emissor e Linux como receptor, por USB. O uso de pressão e a escolha de monitor dependem do hardware, navegador e ambiente gráfico.

## Testes e organização

Execute `make test` para testar o protocolo, a autorização HTTP, a ordem dos traços e a liberação após silêncio. Os testes HTTP precisam poder abrir uma porta em `127.0.0.1`.

O `uv sync` instala as dependências e o pacote Python em modo editável a partir de `src`.

O arquivo `.env` configura a proporção padrão, os tempos de sessão e reconexão e os limites de conexões HTTP. O arquivo `.env.example` contém os valores padrão e pode ser copiado para criar um novo `.env`. Variáveis de ambiente `MESA_*` definidas no sistema têm prioridade.

O receptor segue a arquitetura hexagonal (portas e adaptadores). O domínio contém as regras de desenho. A aplicação usa essas regras e declara as operações de que precisa em `ports.py`. O ponto de composição conecta essas operações às implementações concretas.

| Local | Responsabilidade |
| --- | --- |
| `src/domain/` | Área de desenho, eventos e regras de exclusividade e ordenação da sessão. |
| `src/application/` | Ciclo da sessão USB, reconexão do Android e contratos dos adaptadores. |
| `src/adapters/input/cli.py` | Opções e mensagens de erro da linha de comando. |
| `src/adapters/input/http/` | Servidor local, rotas FastAPI e arquivos da página. As rotas ficam em `routes/`. |
| `src/adapters/output/adb/` | Identificação do Android, túnel reverso e abertura da página via ADB. |
| `src/adapters/output/uinput/` | Caneta e roda virtuais criadas com `evdev.UInput`. |
| `src/startup/bootstrap.py` | Montagem do receptor e encerramento por sinal. |

Consulte as referências do [protocolo do ADB](https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/main/docs/dev/services.md), [encaminhamento no Android](https://developer.android.com/develop/ui/views/layout/webapps/access-local-server), [uinput no kernel Linux](https://docs.kernel.org/input/uinput.html) e [Pointer Events](https://www.w3.org/TR/pointerevents/).
