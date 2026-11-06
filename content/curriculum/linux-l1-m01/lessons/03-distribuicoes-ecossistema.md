## Objetivos desta aula

No fim desta aula deverás conseguir identificar os principais elementos de uma distribuição, explicar o papel dos repositórios e do gestor de pacotes em termos gerais e distinguir famílias de distribuições. O objetivo é reconhecer o ecossistema; a administração detalhada de pacotes será estudada no módulo próprio do mapa original.

## 1. O que uma distribuição entrega?

Uma distribuição combina vários componentes testados e integrados. Dependendo do projeto, pode incluir:

- kernel Linux e módulos;
- bibliotecas de sistema e runtime;
- shell e utilitários básicos;
- gestor de arranque e componentes de inicialização;
- gestor de serviços;
- ferramentas de rede, segurança e administração;
- sistema de pacotes e repositórios;
- configurações, políticas e documentação;
- ciclos de lançamento e manutenção.

A distribuição não é apenas uma marca. É também uma decisão técnica sobre versões, compatibilidade, integração, suporte e atualização.

## 2. Repositório e pacote

Um **pacote** é uma unidade distribuível de software que contém ficheiros, metadados e, frequentemente, instruções de instalação ou remoção. Um **repositório** é uma fonte organizada de pacotes e metadados, utilizada pelo gestor de pacotes.

O **gestor de pacotes** automatiza tarefas como instalar, atualizar, remover e resolver dependências. Uma dependência é outro componente necessário para que um pacote funcione corretamente.

Famílias e exemplos comuns:

| Família / distribuição | Ferramentas comuns | Formato de pacote comum |
| --- | --- | --- |
| Debian / Ubuntu | `apt`, `dpkg` | `.deb` |
| Fedora / RHEL / derivados | `dnf`, `rpm` | `.rpm` |
| SUSE / openSUSE | `zypper`, `rpm` | `.rpm` |
| Arch Linux | `pacman` | `.pkg.tar.*` |
| Alpine Linux | `apk` | `.apk` |

A tabela é uma orientação inicial, não uma regra universal para todos os sistemas derivados. Ferramentas, repositórios e políticas podem variar. Não executes comandos de instalação neste módulo: a gestão de pacotes será ensinada no módulo L1 dedicado a pacotes e software.

## 3. Ciclo de vida e suporte

Uma versão de distribuição tem datas e políticas de manutenção. O conceito **LTS (Long Term Support)** indica uma edição com um período de suporte alargado definido pelo fornecedor do projeto. Não significa “sem necessidade de atualização”, nem garante que qualquer aplicação de terceiros esteja suportada pelo mesmo período.

Em ambiente profissional, verifica sempre:

1. Nome e versão exatos da distribuição.
2. Estado de suporte da versão e calendário oficial.
3. Origem dos pacotes e repositórios habilitados.
4. Política de atualização e janela de manutenção.
5. Compatibilidade com a aplicação, agentes de segurança e ferramentas de observabilidade.

## 4. Como identificar a distribuição corretamente

O ficheiro `/etc/os-release` fornece identificação normalizada da distribuição, incluindo campos como `NAME`, `ID`, `VERSION_ID` e `VERSION_CODENAME`. Já `uname` identifica características do kernel em execução. São fontes diferentes e complementares.

Exemplo de campos comuns num Ubuntu 24.04:

```text
NAME="Ubuntu"
ID=ubuntu
VERSION_ID="24.04"
VERSION_CODENAME=noble
```

O conteúdo exato pode mudar conforme versão e derivado. Usa os valores reais do teu equipamento como evidência; não copies o exemplo como se fosse a tua saída.

## 5. Porque interessa em Cloud e Segurança?

Uma ferramenta de hardening, um agente EDR, um sensor de monitorização ou uma imagem de container pode oferecer suporte apenas a determinadas distribuições, versões e arquiteturas. Um plano de patching também depende do ciclo de vida da distribuição e do kernel.

Um inventário que diga apenas “Linux” é insuficiente para decisões de suporte e risco. O registo profissional deve separar distribuição, release, kernel, arquitetura e papel do sistema.

## Verificação da aprendizagem

Explica a diferença entre distribuição, pacote, repositório e gestor de pacotes. Depois indica que campos de `/etc/os-release` usarias para identificar uma instalação e por que razão `uname -r` não substitui essa identificação.
