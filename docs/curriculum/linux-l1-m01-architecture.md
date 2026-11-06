# Linux L1 — Módulo 1: Arquitetura e ecossistema

Este módulo é a primeira unidade integral de referência do CloudSec Range. Mantém a posição, identificador, título e carga horária original do mapa canónico: **L1 / M1 / 6 horas**.

## Fonte e documentação oficial

O conteúdo foi elaborado a partir da documentação primária do kernel Linux, GNU, Ubuntu, systemd e Microsoft WSL. Os links são registados em `content/curriculum/linux-l1-m01/module.json` e importados para `learning_resources`.

## Conteúdo incluído

- 6 aulas com explicações, terminologia e verificações da aprendizagem;
- 6 competências com pré-requisitos e requisitos de cobertura para ambos os centros;
- 2 laboratórios seguros para WSL 2 e Ubuntu 24.04;
- 1 ticket profissional simulado para a Nexus Digital Services;
- 1 avaliação mista de 100 pontos com perguntas, grelha e erros críticos;
- 9 referências oficiais;
- relações explícitas entre competências, aulas, laboratórios, ticket e avaliação.

## Importação

A importação é chamada pelo `seed_curriculum.py` após a importação do mapa canónico. É aditiva e idempotente: cria apenas registos em falta e não elimina dados. Registos já existentes não são sobrescritos pelo seed, para proteger autoria posterior. Alterações de conteúdo devem ser revistas e publicadas como nova versão editorial.

## Estado de qualidade

O conteúdo inicia em `draft`. O ticket fica em `backlog`, os laboratórios em `planned` e a avaliação em `planned`. Nenhuma competência é marcada como dominada, verificada ou concluída automaticamente. A evidência só pode ser registada depois de a prática ser realizada e revista.

## Âmbito de segurança

Os laboratórios são somente de inventário e documentação local. Não executam `sudo`, não instalam pacotes, não alteram configuração, serviços, kernel, bootloader, rede ou armazenamento. O Lab 2 cria os artefactos apenas em `~/cloudsec-range-labs/linux-m01`.

## Regra de domínio

A aprovação exige pelo menos 80/100, ausência de erros críticos não corrigidos e demonstração prática. A avaliação não é autocorrigida nesta versão. A revisão deve identificar, para cada resposta, acerto/erro/incompletude, pontuação justificada, lacuna e reforço necessário.
