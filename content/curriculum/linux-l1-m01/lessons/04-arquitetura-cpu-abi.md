## Objetivos desta aula

No fim desta aula deverás conseguir distinguir arquitetura de CPU, arquitetura reportada pelo kernel, arquitetura de pacotes e ABI. Deverás compreender por que uma aplicação compilada para uma arquitetura pode não executar noutra, mesmo quando ambas usam Linux.

## 1. Arquitetura de hardware

A **arquitetura de CPU** define um conjunto de instruções e regras fundamentais que o processador entende. Exemplos atuais importantes são:

- **x86_64** (também chamado AMD64): arquitetura de 64 bits da família x86, comum em muitos computadores e servidores.
- **AArch64** (frequentemente designado ARM64): arquitetura de 64 bits do ecossistema ARM, utilizada em muitos dispositivos e também em servidores e instâncias cloud.

Não confundas fabricante e arquitetura. Intel e AMD podem executar a arquitetura x86_64; ARM é uma família de arquitetura, não o nome de uma distribuição Linux.

## 2. Nome da arquitetura no kernel e no gestor de pacotes

Os nomes não são sempre idênticos entre ferramentas. Num sistema Debian/Ubuntu x86_64, por exemplo:

- `uname -m` pode apresentar `x86_64`;
- `dpkg --print-architecture` pode apresentar `amd64`.

Num sistema ARM de 64 bits, podes encontrar `aarch64` no kernel e `arm64` no ecossistema Debian. A diferença de nome não significa, por si só, incompatibilidade.

## 3. O que é ABI?

A **Application Binary Interface (ABI)** define regras que componentes binários precisam de seguir para interagir numa plataforma. Inclui aspetos como convenções de chamada, representação de dados, convenções de ligação e interfaces entre programa, bibliotecas e sistema.

Para executar um binário, não basta existir um kernel Linux. A arquitetura, o formato do binário, a ABI, as bibliotecas necessárias e a compatibilidade do sistema têm de ser adequados.

## 4. Exemplo de operação

Imagina que uma equipa constrói uma imagem de container para `amd64`, mas o servidor de destino é `arm64`. O kernel Linux pode suportar ambas as arquiteturas, mas o binário dentro da imagem pode não executar nativamente no destino. A plataforma de containers ou a camada de emulação pode apresentar um erro, ou a execução pode exigir uma imagem multi-arquitetura apropriada.

Em Cloud, escolher entre instâncias x86_64 e ARM64 influencia compatibilidade de imagens, agentes de segurança, bibliotecas nativas, extensões e custos/desempenho. A decisão deve ser validada com os fornecedores e testes reais.

## 5. Comandos para observar a arquitetura

```bash
uname -m
getconf LONG_BIT
dpkg --print-architecture
```

Interpretação:

- `uname -m`: nome da arquitetura que o kernel reporta.
- `getconf LONG_BIT`: largura de bits da interface C para o ambiente consultado, normalmente 64 num Ubuntu 64 bits.
- `dpkg --print-architecture`: arquitetura principal que o sistema de pacotes Debian utiliza.

Não concluas que a máquina física é necessariamente a mesma arquitetura apenas porque estás dentro de uma distribuição. Em virtualização e emulação, a arquitetura apresentada ao guest e a arquitetura do host podem diferir. Regista exatamente o contexto observado.

## Verificação da aprendizagem

Explica por que `x86_64` e `amd64` podem descrever o mesmo alvo de 64 bits em ferramentas diferentes. Depois descreve uma consequência operacional de tentar executar um binário construído para a arquitetura errada.
