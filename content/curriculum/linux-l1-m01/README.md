# Linux L1 · Módulo 1 — Arquitetura e ecossistema

**Fonte curricular:** `Cronograma de estudo — Redes e Linux (1).pdf` (L1, M1, 6 horas). O identificador e a posição do módulo não foram alterados.

## Estrutura pedagógica

| Aula | Título | Tempo planeado |
|---|---|---:|
| 01 | Sistema operativo, GNU e Linux | 35 min |
| 02 | Espaço de utilizador, kernel e system calls | 40 min |
| 03 | Distribuições e ecossistema | 35 min |
| 04 | Arquitetura de CPU e ABI | 30 min |
| 05 | Arranque e init — visão arquitetural | 35 min |
| 06 | WSL 2 e fronteiras de segurança | 45 min |
| Lab 1 | Inventário de arquitetura (somente leitura) | 35 min |
| Lab 2 | Mapa de arquitetura e relatório de evidências | 45 min |
| Avaliação | Avaliação teórica e prática mista | 60 min |
| **Total** |  | **360 min (6 h)** |

## Critério de domínio

A unidade não está dominada apenas por leitura ou conclusão dos laboratórios. Exige explicação oral/escrita correta, execução autónoma de comandos de inventário, interpretação das saídas, resolução de um cenário de troubleshooting, conclusão do ticket simulado, avaliação com pelo menos 80/100 e evidências revistas. Uma resposta que confunda kernel com distribuição, ou `sudo` com Administrador do Windows, exige reforço antes de aprovação.

## Segurança

Os dois laboratórios são de inventário e documentação. Não alteram kernel, serviços, bootloader, partições, pacotes ou políticas do host. Não usar `sudo`, não instalar ferramentas e não modificar `/etc`, `/boot`, `/proc` ou configurações do WSL. O segundo laboratório cria apenas ficheiros numa pasta do utilizador.
