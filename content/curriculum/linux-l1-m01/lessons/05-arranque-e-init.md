## Objetivos desta aula

No fim desta aula deverás descrever, em alto nível, o percurso típico de arranque de um sistema Linux tradicional e distinguir kernel de gestor de serviços. O estudo detalhado de arranque, kernel, módulos, processos e `systemd` será aprofundado nos módulos próprios do mapa; aqui estabelecemos o modelo arquitetural.

## 1. Sequência típica de arranque num servidor físico ou VM tradicional

Uma sequência simplificada é:

1. **Firmware (BIOS/UEFI):** inicializa o hardware e escolhe um dispositivo ou entrada de arranque.
2. **Bootloader (gestor de arranque):** carrega o kernel e, quando necessário, a imagem de initramfs.
3. **Kernel:** inicializa estruturas internas, deteta/configura recursos e prepara a execução do espaço de utilizador.
4. **Initramfs (initial RAM filesystem):** ambiente temporário que pode fornecer drivers e ferramentas necessários para localizar e montar o sistema de ficheiros raiz.
5. **Sistema de ficheiros raiz:** disponibiliza o ambiente principal do sistema.
6. **Processo PID 1:** primeiro processo do espaço de utilizador, que assume responsabilidades de inicialização e gestão do sistema.
7. **Serviços e sessões:** são iniciados os serviços e os ambientes de execução necessários.

Esta sequência é um modelo geral. Distribuições, bootloaders, initramfs, plataformas cloud e ambientes virtualizados podem introduzir diferenças. Não uses este diagrama como prova de que o WSL 2 arranca exatamente como uma máquina física.

## 2. O que é PID 1?

Cada namespace de processos tem uma visão dos identificadores de processo. No namespace principal de um sistema Linux tradicional, o primeiro processo de espaço de utilizador tem PID 1. É um processo especial: participa na inicialização do sistema e adota processos órfãos conforme as regras do sistema.

O processo PID 1 pode ser `systemd`, mas não tem obrigatoriamente de ser. Outras implementações de init existem. Por isso, nunca assumas que `systemctl` está disponível ou que `systemd` é o gestor ativo sem verificar.

## 3. O que é systemd?

**systemd** é uma suite de componentes que inclui um gestor de sistema e serviços. Em sistemas que o utilizam como init principal, executa como PID 1 e inicia e coordena serviços. Também integra componentes relacionados com logs, sockets, montagens, temporizadores e outras funções de sistema.

O kernel e `systemd` não são a mesma coisa:

- O kernel é o núcleo privilegiado do sistema operativo.
- `systemd` é software de espaço de utilizador, executado com privilégios apropriados, que coordena inicialização e serviços.
- Um serviço é um processo ou conjunto de processos que fornece uma função, por exemplo, SSH ou uma API web.

## 4. Verificação segura

```bash
ps -p 1 -o pid=,comm=,args=
```

O comando pede ao `ps` que mostre o processo com PID 1, incluindo o identificador, nome curto e argumentos. O resultado observado é a evidência; não substituas o resultado esperado por uma suposição. Se a saída indicar `systemd`, podes depois consultar `systemctl --version`, mas não é necessário alterar qualquer serviço neste módulo.

## 5. Limite deste módulo

Não vamos editar GRUB, initramfs, módulos do kernel, serviços ou unidades `systemd`. Essas ações podem impedir o arranque ou afetar serviços e pertencem a módulos posteriores com laboratórios isolados e procedimentos de recuperação. Neste primeiro módulo, queremos compreender a arquitetura e recolher informação sem modificar o sistema.

## Verificação da aprendizagem

Desenha o percurso firmware → bootloader → kernel → initramfs → sistema raiz → PID 1 → serviços. Explica o que pode variar numa distribuição e por que `systemd` não deve ser tratado como sinónimo de kernel.
