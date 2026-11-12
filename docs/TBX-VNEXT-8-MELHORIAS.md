# TBX Edition — Próxima versão experimental (Starling 0.8.0)

**Estado:** preparação de código-fonte, **SEM APK**. Branch: `experiment/starling-v080-tbx-blue-ui`.

Base: Starling v0.8.0 fixada no commit `ac874422ed8f892505ff73d67ae486ecfee7a516`. **Não é a fonte original aprovada da V1.0.4 da TBX Edition**. Não publicar como atualização instalável sem recuperar/mesclar o projeto original, verificar identidade/assinatura e compilar/testar no Android.

## Lista das oito alterações pedidas

| Pedido | O que foi feito no código | Falta validar ou implementar |
| --- | --- | --- |
| 1. Otimizador de shaders | `apply_tbx_optimizations_vnext.py`: ajuste conservador do perfil automático em GPUs intermediárias/fracas, limitando custo de sombras sem desligar água e iluminação. Remoção da redução **automática** de resolução que o Starling fazia ao usar shader Auto; permanece a resolução escolhida no menu. | Autoajuste em tempo real por FPS/GPU, compatibilidade com MakeUp Ultra Fast e benchmarks reais. Não prometer 60 FPS. |
| 2. FPS estável | No Android, uploads de terreno/chunks sempre atravessam o orçamento de tempo já existente do motor para evitar rajadas no thread da interface. | Teste de FPS médio, percentil 1%, tempo de GPU, carregamento de chunks, RAM e regressões. |
| 3. Controles rápidos | A proteção prévia de troca de tela foi mantida; agora toques de menu que só terminam mais de 1,5s depois do início não produzem um clique tardio. | Testes reais de arrastar, manter pressionado, mudar de tela, toque fantasma; não corrige falhas do touchscreen do Android fora do jogo. |
| 4. Água e sombras | Limites de sombra reduzidos para Auto em GPUs menores, preservando os cálculos de água e luz do shader em jogo. | **Pendente:** melhoria visual específica de reflexos, ondas, alinhamento solar e sombra completa — shaders diferentes exigem integração própria. Nada disso foi provado corrigido. |
| 5. Recuperação automática | Mantida a proteção nativa que desliga o shader que falhar ou perder o dispositivo gráfico. Adicionado registro local da última desativação para diagnóstico, sem apagar mundos. | Teste de tela preta/crash em drivers diferentes e eventual opção de restaurar o último perfil seguro. |
| 6. Instalador de mods | Catálogo Starling continua resolvendo dependências de mods compatíveis. Ferramenta adicional `tbx_mod_install_preflight.py` informa dependências declaradas por `.jar` Fabric/Quilt/Forge, sem executar código Java nem alegar conversão para Rust. | **Pendente:** integrar pré-verificação ao menu, seleção/instalação em lote e conversão real de código Java para hooks Rust. O `.jar` não vira automaticamente um mod jogável. |
| 7. Backup dos mundos | Usado o worker de backup ZIP existente no Starling. Para Android, faz uma primeira cópia ao abrir um mundo compatível e somente tenta outra depois de sete dias de backup bem-sucedido. Não bloqueia o thread de renderização enquanto compacta, mas pode atrasar a entrada no mundo e ocupar armazenamento. | Testar com mundos grandes/pouco armazenamento, restauração e criar opção de ativar/desativar a rotina. |
| 8. Ender Dragon | `apply_tbx_dragon_visibility.py`: o corpo do dragão deixa de depender da textura opcional dos olhos brilhantes. Se a textura dos olhos faltar, o corpo ainda pode ser desenhado. | **Pendente:** confirmar modelo e skin presentes, voar, colisão, dano, barra de vida, cristais e batalha inteira no Android. |

## Passos reais e verificáveis

- Ferramentas do patch da próxima versão: `tools/apply_tbx_optimizations_vnext.py`, `tools/apply_tbx_resilience_vnext.py`, `tools/tbx_backup.rs`, `tools/apply_tbx_dragon_visibility.py`, `tools/tbx_mod_install_preflight.py`.
- CI `.github/workflows/tbx-starling-source-only.yml`: baixa código upstream fixado, executa validação da sintaxe das ferramentas, testes Python, aplica patches idempotentes, chama Rustfmt como validador de **sintaxe** em Rust e gera arquivo compactado do código.
- Rustfmt **não é** teste de compilação, linkedição nem execução do jogo.
- A partir da conclusão de um build de código **não se deve dizer que os 8 recursos ficaram prontos**, que alcançamos 60 FPS ou que um bug foi resolvido no celular.
- A ideia **Mundo Permanente** cancelada pelo usuário continua fora da branch e fora da workflow.
- Nenhum APK foi criado nesta rodada.

## Próximas prioridades sugeridas

1. Compilação de testes Rust em ambiente compatível, quando o projeto e recursos estiverem disponíveis, mantendo o pedido de **não criar APK**.
2. Validar Android e comparar o funcionamento com/sem shader em menus, carregamento e recuperação.
3. Testar completamente Ender Dragon e shader escolhido antes de alterações que mexam em mecânicas/estética.
4. Criar configurações claras para os backups e uma página unificada de compatibilidade de mods.
