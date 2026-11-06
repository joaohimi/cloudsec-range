## Objetivos desta aula

No fim desta aula deverás conseguir distinguir **espaço de utilizador** e **espaço de kernel**, explicar por que existem níveis de privilégio e descrever o papel de uma **chamada de sistema** (system call). Não precisas de programar chamadas de sistema neste módulo; precisas de compreender a fronteira que elas representam para administração, troubleshooting e segurança.

## 1. Porque é que existe separação?

Se qualquer aplicação pudesse executar livremente operações privilegiadas, um erro num programa poderia comprometer todo o sistema: sobrescrever memória do kernel, controlar diretamente dispositivos ou interferir com outros processos. Os processadores modernos e o kernel implementam mecanismos de proteção para separar código menos privilegiado de operações privilegiadas.

O **espaço de utilizador (user space)** é o ambiente onde normalmente executam aplicações, shells, ferramentas, bibliotecas e serviços. Cada processo tem o seu contexto e não deve aceder livremente à memória de outros processos nem controlar diretamente o hardware.

O **espaço de kernel (kernel space)** é a região privilegiada onde o kernel executa as operações que precisam de controlo centralizado: escalonamento, memória, dispositivos, sistemas de ficheiros e rede, entre outras.

Esta separação não significa que o espaço de utilizador seja automaticamente seguro. Uma aplicação vulnerável pode ser explorada, roubar dados acessíveis ao seu utilizador ou abusar de permissões concedidas. Significa que existe uma fronteira de proteção e que o acesso a operações privilegiadas passa por interfaces controladas.

## 2. O que é uma chamada de sistema?

Uma **chamada de sistema (system call)** é uma interface controlada pela qual um programa solicita um serviço ao kernel. Exemplos de operações que normalmente envolvem chamadas de sistema incluem abrir ou ler ficheiros, criar processos, comunicar através de sockets e alterar atributos de ficheiros.

O percurso conceptual é:

1. A aplicação executa em espaço de utilizador.
2. A aplicação chama uma função de biblioteca ou uma interface que necessita de um serviço do kernel.
3. A biblioteca prepara os argumentos e aciona a interface de chamada de sistema adequada.
4. O processador passa para o contexto privilegiado de execução do kernel.
5. O kernel valida os argumentos e as permissões, executa ou rejeita a operação e produz um resultado.
6. O controlo regressa ao espaço de utilizador, onde a aplicação trata o resultado.

Uma chamada de sistema não é o mesmo que um comando do terminal. `cat` é um programa; `read` é também o nome de uma chamada de sistema Linux. O programa pode utilizar funções de biblioteca que, internamente, recorrem a chamadas de sistema.

## 3. Funções de biblioteca e chamadas de sistema

Uma **biblioteca** é um conjunto de funções reutilizáveis. A glibc, por exemplo, é a biblioteca C GNU utilizada por muitos programas em sistemas GNU/Linux. Uma função de biblioteca pode preparar dados, aplicar compatibilidade entre versões e chamar uma ou mais interfaces do kernel.

Portanto, não assumas que cada função de biblioteca corresponde a uma chamada de sistema com o mesmo nome, nem que cada comando do terminal corresponde a uma única chamada. A relação pode ser mais complexa.

## 4. Exemplo completo: ler um ficheiro

Quando executas:

```bash
cat /etc/os-release
```

O fluxo simplificado é:

- O shell localiza e inicia o programa `cat` (quando `cat` é um executável externo).
- `cat` solicita ao sistema a abertura do caminho `/etc/os-release`.
- O kernel verifica a resolução do caminho e as permissões aplicáveis.
- O programa lê os dados e escreve o resultado no terminal, que é a saída padrão.
- O programa termina e devolve um código de saída ao shell.

Este exemplo atravessa várias camadas: shell, programa, biblioteca, chamadas de sistema, kernel, sistema de ficheiros e dispositivo/terminal. Os detalhes internos exatos dependem do programa e da implementação; o modelo serve para raciocinar, não para afirmar que existe sempre uma sequência fixa de chamadas.

## 5. Implicações operacionais e de segurança

- Um erro `Permission denied` pode resultar de verificações de permissões no kernel, mas a causa pode estar no utilizador, grupo, ACL, montagem ou política de segurança. Não concluas automaticamente que é preciso usar `sudo`.
- Um processo em espaço de utilizador pode consumir CPU, memória e rede; o kernel continua a gerir e contabilizar esses recursos.
- Uma falha numa aplicação não significa necessariamente que o kernel falhou.
- Uma vulnerabilidade no kernel tem potencial de impacto maior do que uma falha limitada a um processo sem privilégios, porque o kernel ocupa a camada privilegiada.
- A concessão de privilégios elevados deve ser mínima: um processo não deve receber mais autoridade do que precisa.

## Terminologia essencial

- **Privilégio:** nível de autoridade que permite executar determinadas operações.
- **Processo:** instância de um programa em execução, com estado e recursos associados.
- **Biblioteca:** código reutilizável que fornece funções a programas.
- **ABI (Application Binary Interface):** regras de baixo nível que permitem que binários, bibliotecas e componentes interajam numa plataforma, incluindo convenções de chamada e formatos esperados.
- **Código de saída:** valor numérico devolvido por um programa ao terminar; por convenção, zero indica sucesso e valores diferentes de zero indicam alguma condição de erro ou resultado especial.

## Verificação da aprendizagem

Desenha o percurso de `cat /etc/os-release` e identifica pelo menos quatro componentes. Depois explica por que razão uma aplicação normal não deve ter acesso irrestrito às operações privilegiadas do kernel.
