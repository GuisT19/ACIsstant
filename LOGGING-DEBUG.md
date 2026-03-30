# Padrão de Logging e Debug — ACIsstant

## Objetivo
Garantir rastreabilidade, diagnóstico rápido e manutenção eficiente do backend.

## Níveis de Log
- **INFO**: Operações normais, inicializações, sucesso de endpoints, status de recursos.
- **WARNING**: Situações inesperadas, mas não críticas (ex: recurso não encontrado, operação ignorada).
- **ERROR**: Falhas em operações, exceções capturadas, problemas de dependências.
- **CRITICAL**: Erros fatais, falha de inicialização, crash do servidor.

## Boas Práticas
- Sempre use o logger do módulo (`logger = logging.getLogger("acisstant.[modulo]")`).
- Inclua contexto relevante: IDs, nomes de arquivos, parâmetros críticos.
- Para exceções, sempre registre o traceback (`logger.error(..., exc_info=True)` se necessário).
- Não exponha dados sensíveis nos logs.
- Use logs para todas as operações de IO, inicialização, carregamento de modelos, queries e manipulação de dados.

## Exemplo de Log
```
[2026-03-30 14:00:00] INFO: [DB] Chat created: 1234 ('Novo Chat')
[2026-03-30 14:00:01] WARNING: [RAG] Query attempted but vector_store is not loaded.
[2026-03-30 14:00:02] ERROR: [LLM] Failed to load model: FileNotFoundError('...')
[2026-03-30 14:00:03] CRITICAL: [UNHANDLED ERROR] ... Traceback: ...
```

## Debug
- Todos os erros não tratados são capturados pelo middleware global e registrados com traceback.
- O frontend recebe resposta padronizada de erro, com tipo e últimas linhas do traceback.
- Use os endpoints `/api/health` e `/api/status` para monitoramento e diagnóstico rápido.

## Onde encontrar os logs
- Por padrão, logs são enviados para o terminal onde o backend está rodando.
- Para produção, configure o logging para salvar em arquivo se necessário.

---
Dúvidas ou sugestões? Atualize este documento para manter o padrão alinhado com a equipe.
