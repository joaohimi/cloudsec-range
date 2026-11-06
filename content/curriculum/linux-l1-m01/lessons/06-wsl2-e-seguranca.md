## Objetivos desta aula

No fim desta aula deverás explicar a relação entre Windows host, máquina virtual gerida pelo WSL 2, kernel Linux e distribuição Ubuntu. Também deverás identificar que fronteiras de isolamento existem e quais são as limitações de segurança que impedem tratar WSL 2 como substituto automático de uma VM de produção isolada.

## 1. Componentes do teu ambiente

No teu laboratório, existem vários níveis:

- **Windows host:** o sistema operativo principal do computador.
- **WSL (Windows Subsystem for Linux):** funcionalidade do Windows que permite executar ambientes GNU/Linux integrados com o Windows.
- **WSL 2 managed VM:** máquina virtual leve, gerida pelo WSL, que fornece o ambiente onde corre o kernel Linux.
- **Kernel Linux do WSL 2:** kernel Linux fornecido/atualizado pelo mecanismo WSL e baseado no código-fonte do kernel Linux.
- **Distribuição Ubuntu:** sistema de ficheiros e conjunto de programas, bibliotecas, configurações e serviços da distribuição.
- **Utilizador Linux:** identidade dentro da distribuição, como `joao`; não é automaticamente a identidade Administrador do Windows.

A distribuição não é uma VM tradicional que tenhas de administrar como um servidor Hyper-V independente. O WSL gere a máquina virtual de suporte.

## 2. O que o WSL 2 partilha e o que isola?

De acordo com a documentação da Microsoft, as distribuições WSL 2 executam como ambientes isolados dentro da VM gerida. As distribuições partilham, entre outros elementos, o kernel, CPU, memória, swap e namespace de rede; possuem namespaces próprios de PID, mount, user e cgroup e o seu próprio processo init. Existem exceções específicas, como `/dev/pts`, descritas na documentação.

Isto é importante: duas distribuições WSL 2 não equivalem a duas VMs com kernels independentes. Uma atualização do kernel gerido pelo WSL pode afetar as distribuições que o utilizam. A partilha do kernel é uma diferença arquitetural relevante para o modelo de isolamento.

## 3. Fronteira entre Linux e Windows

O WSL integra os dois ambientes. É possível, conforme configuração, aceder a ficheiros do Windows através de pontos de montagem como `/mnt/c` e invocar ferramentas Windows a partir do Linux. Esta integração é produtiva, mas significa que as fronteiras de ficheiros e identidade devem ser entendidas corretamente.

- `/home/joao` pertence ao sistema de ficheiros Linux da distribuição.
- `/mnt/c/Users/DP` representa uma localização do volume C: do Windows montada no ambiente Linux.
- `sudo` eleva privilégios dentro do contexto Linux da distribuição. Não transforma a sessão num Administrador do Windows.
- As permissões efetivas em ficheiros montados do Windows dependem também do modelo de montagem e das ACLs do Windows; não assumas que as regras POSIX se comportam exatamente como num sistema de ficheiros Linux nativo.

Para projetos e ferramentas Linux, guardar o projeto no sistema de ficheiros Linux (por exemplo, em `~/projects`) é normalmente a opção recomendada para desempenho e semântica Linux, conforme a documentação WSL. Isso não significa que o volume Windows não possa ser usado; significa que deves escolher conscientemente o local.

## 4. O que WSL 2 é adequado a fazer — e o que não deves presumir

WSL 2 é adequado para desenvolvimento, aprendizagem, execução de ferramentas Linux e laboratórios locais controlados. Não assumas que equivale a:

- uma máquina física Linux;
- uma VM de produção com rede e armazenamento independentes;
- uma fronteira de isolamento multi-tenant para executar código hostil;
- um ambiente cloud real, com IAM, rede virtual, políticas e controlos de conta cloud;
- uma cópia exata do processo de arranque de um servidor tradicional.

Para experiências de kernel, ataques a nível de host, malware ou alterações que possam comprometer o sistema, utiliza uma VM descartável dedicada e isolada, não o WSL de trabalho.

## 5. Recolha de evidências no WSL

Dentro do Ubuntu:

```bash
uname -r
uname -m
cat /etc/os-release
ps -p 1 -o pid=,comm=,args=
systemd-detect-virt
```

No PowerShell do Windows:

```powershell
wsl --status
wsl --list --verbose
```

As duas perspetivas são complementares: os comandos Linux identificam o kernel e a distribuição vistos do ambiente Linux; os comandos WSL mostram as distribuições instaladas e a versão WSL atribuída a cada uma.

Se `systemd-detect-virt` não existir, regista essa ausência e utiliza as outras evidências. Não instales pacotes para contornar uma falha durante este módulo.

## 6. Implicações de segurança para DevOps e Cloud Security

1. **Identidade:** distingue conta Linux, utilizador Windows e identidade cloud. São autoridades diferentes.
2. **Kernel partilhado:** não assumes isolamento de kernel entre distribuições WSL 2.
3. **Acesso a ficheiros:** trata caminhos Windows montados com o mesmo cuidado que dados locais; evita guardar segredos em locais sincronizados ou acessíveis a utilizadores não autorizados.
4. **Ambiente de produção:** não uses WSL como prova de que uma aplicação foi validada num servidor de produção equivalente.
5. **Inventário:** regista distribuição, release, kernel, arquitetura e camada de virtualização separadamente.
6. **Laboratórios:** mantém exercícios de segurança ofensiva em ambientes descartáveis e isolados, com âmbito explícito.

## Verificação da aprendizagem

Explica a arquitetura Windows → WSL 2 managed VM → kernel Linux → distribuição Ubuntu. Depois indica três diferenças entre WSL 2 e uma VM tradicional independente e duas implicações de segurança da partilha do kernel e da integração de ficheiros.
