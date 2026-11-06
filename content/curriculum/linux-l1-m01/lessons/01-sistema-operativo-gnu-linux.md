## Objetivos desta aula

No fim desta aula deverás conseguir explicar, sem confundir os termos, o que é um sistema operativo, o que é um kernel, o que significa GNU/Linux e o que é uma distribuição Linux. Também deverás conseguir explicar por que motivo instalar apenas o kernel Linux não equivale a instalar um sistema utilizável para administração de servidores.

## 1. O que é um sistema operativo?

Um **sistema operativo (SO)** é o conjunto de componentes de software que gere os recursos de um computador e fornece serviços às aplicações. Os recursos incluem CPU, memória RAM, dispositivos de armazenamento, interfaces de rede e dispositivos de entrada/saída.

Uma aplicação não deve ter de controlar diretamente cada modelo de disco, placa de rede ou processador. O sistema operativo oferece interfaces consistentes para que os programas peçam serviços, enquanto o sistema operativo coordena o acesso aos recursos e aplica mecanismos de proteção.

Um SO completo inclui mais do que o kernel. Inclui ferramentas de administração, bibliotecas, serviços, mecanismos de arranque, configuração e aplicações básicas. A composição concreta varia conforme o produto e a distribuição.

## 2. O que é o kernel?

O **kernel** (núcleo) é a componente central do sistema operativo. É carregado durante o arranque e permanece ativo enquanto o sistema funciona. Entre as suas responsabilidades principais estão:

- **Gestão de processos e escalonamento:** decide quando cada processo pode utilizar o CPU e gere a criação, execução e término de processos.
- **Gestão de memória:** controla a memória virtual, protege os espaços de memória dos processos e gere a memória física.
- **Abstração de dispositivos:** fornece interfaces para que o restante sistema utilize hardware através de drivers e subsistemas.
- **Sistemas de ficheiros:** fornece operações e abstrações para aceder a ficheiros, diretórios e dispositivos de armazenamento.
- **Rede:** implementa grande parte da pilha de rede, sockets e protocolos suportados pelo kernel.
- **Controlo de acesso e isolamento:** aplica verificações de permissões e mecanismos de isolamento disponibilizados pelo kernel.

No contexto deste curso, quando dizemos **Linux**, em sentido técnico estrito estamos normalmente a referir-nos ao kernel Linux. O kernel, isoladamente, não contém toda a experiência de uma distribuição pronta para utilização.

## 3. GNU, bibliotecas e ferramentas de espaço de utilizador

O ecossistema GNU fornece muitas ferramentas e componentes comuns em sistemas GNU/Linux, como shells, compiladores e utilitários de linha de comandos. A **biblioteca C** (por exemplo, glibc em muitas distribuições) fornece funções utilizadas por programas para interagir com o ambiente do sistema; algumas dessas funções acabam por solicitar serviços ao kernel através de chamadas de sistema.

É por isso que a expressão **GNU/Linux** é tecnicamente utilizada para descrever muitos sistemas que combinam o kernel Linux com ferramentas e bibliotecas do projeto GNU e de outros projetos. Na linguagem corrente, é frequente chamar simplesmente Linux ao sistema completo. O importante para um profissional é perceber que kernel, biblioteca, ferramentas e distribuição são componentes diferentes, com versões e ciclos de atualização próprios.

Nem todas as distribuições utilizam exatamente os mesmos componentes. Por exemplo, podem escolher bibliotecas, shells, gestores de serviços, ferramentas de rede e modelos de configuração diferentes.

## 4. O que é uma distribuição Linux?

Uma **distribuição** (distro) integra o kernel Linux com um conjunto selecionado de componentes, ferramentas, configurações, repositórios e políticas de manutenção, de modo a entregar um sistema instalável e administrável.

Uma distribuição costuma definir, entre outros aspetos:

1. Que kernel ou conjunto de kernels é fornecido e como recebe atualizações.
2. Que bibliotecas e ferramentas de espaço de utilizador são incluídas.
3. Como os pacotes são construídos, assinados, distribuídos e instalados.
4. Que gestor de serviços e configuração é usado por omissão.
5. Como são publicadas versões, atualizações de segurança e períodos de suporte.

**Exemplo:** Ubuntu 24.04 LTS é uma distribuição e versão específica. O kernel em execução dentro dessa instalação pode ter uma versão diferente da versão originalmente fornecida no lançamento, por causa de atualizações e do modelo de kernel utilizado. Portanto, “Ubuntu 24.04” e “Linux 6.x” não são respostas concorrentes: descrevem camadas diferentes.

## 5. Modelo mental: camadas, não nomes misturados

Pensa num servidor de aplicação:

- O hardware disponibiliza CPU, RAM, armazenamento e interfaces de rede.
- O kernel controla o acesso a esses recursos.
- As bibliotecas e ferramentas de espaço de utilizador fornecem interfaces reutilizáveis.
- Os serviços e aplicações executam tarefas de negócio, por exemplo, uma API web.
- A distribuição integra e mantém estes componentes como um sistema coerente.

Este modelo ajuda a localizar problemas. Uma incompatibilidade de binário pode estar relacionada com arquitetura/ABI; uma falha de serviço pode estar no processo ou no gestor de serviços; uma falha de driver pode envolver o kernel; uma versão de ferramenta pode pertencer ao repositório da distribuição.

## 6. O que não deves confundir

- **Linux não é sinónimo de Ubuntu.** Ubuntu é uma distribuição que usa o kernel Linux.
- **Kernel não é distribuição.** O kernel é apenas uma das componentes fundamentais do sistema.
- **Distribuição não é ambiente desktop.** GNOME, KDE e outros ambientes gráficos são componentes opcionais; um servidor pode não ter interface gráfica.
- **Versão da distribuição não é versão do kernel.** Regista ambas separadamente.
- **Terminal não é o sistema operativo.** O terminal é uma interface; o shell interpreta comandos, e os programas executam operações no sistema.

## Exemplo prático explicado

Quando um administrador executa `cat /etc/os-release`, o comando `cat` é um programa de espaço de utilizador. Ele pede ao sistema operações sobre o ficheiro; a biblioteca utilizada pelo programa interage com o kernel através das interfaces disponíveis. O kernel valida as operações, acede ao sistema de ficheiros e devolve os dados. O texto lido identifica a distribuição e a sua versão, não a versão do kernel.

## Verificação da aprendizagem

Explica oralmente, sem consultar esta aula:

1. O que é o kernel e que responsabilidades tem?
2. Porque é que um kernel Linux isolado não equivale a uma distribuição pronta?
3. Que informação descreve `Ubuntu 24.04` e que informação descreve `Linux 6.x`?
4. Que problema profissional pode surgir se um inventário registar apenas “Linux” sem versão da distribuição e kernel?
