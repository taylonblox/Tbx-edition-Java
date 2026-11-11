# TBX Edition — Mundo Permanente (não “Servidor” na interface)

## Objetivo do usuário

No **Multijogador**, um botão **+** no canto superior direito, com a **mesma textura padrão dos botões Java**. Ao tocar, abre a **tela existente de Criar mundo** (abas Jogo, Mundo, Mais; seed, modo, regras, packs e demais opções). O botão de conclusão passa a se chamar **Criar mundo permanente**. Depois, a pessoa escolhe um **endereço desejado**.

O mundo deve continuar acessível mesmo sem o criador ou um amigo conectados e sem exigir conta Microsoft do jogador. O nome visível é *Mundo Permanente*, não servidor.

## O que está realmente no código Starling experimental

- Implementação de UI: `tools/apply_tbx_permanent_world_wizard.py` e `tools/tbx_permanent_world.rs`.
- Reutiliza os botões vanilla via `Title::buttons` e a tela `create_world::buttons`, não imagens semelhantes ou outro aplicativo.
- Abre a tela de escolher endereço depois de confirmar as opções do mundo.
- Aceita somente um identificador **pedido**, seguro, de 3 a 32 caracteres (`meu-mundo`). Não é domínio DNS, não está reservado e não é link funcional.
- Salva **rascunho** do pedido em JSON local com nome, seed, modo e `WorldOptions` completos para provisionamento futuro.
- Traduções para português/inglês obedecem ao idioma do jogo. 
- **Sem APK**. A versão V1.0.4 da TBX não foi alterada.

## O que NÃO funciona ainda (não alegar pronto)

- Mundo 24/7 para outras pessoas, mesmo com todos offline: requer serviço **remoto sempre ativo** com processo persistente, armazenamento durável e conectividade pública; o celular não precisa ficar online *depois* de aprovisionado.
- Provisionamento em uma hospedagem real, escolha/registro de endereço público e preço/cota do host.
- Conexão de jogo offline sem Microsoft: precisa de mecanismo de identidade/convites e controle de acesso próprios (sem fingir que o serviço de autenticação do Minecraft foi resolvido).
- Sincronização de mundos, backup, atualizações de versão, proteção contra invasões, limite de jogadores, modpack compatível, regras de acesso e remoção do mundo.
- Backend que receba o pedido, valide endereço disponível, crie o mundo remoto com as opções selecionadas, informe estado real e devolva endereço de conexão.
- Compilação/testes Android do código Rust novo. A validação atual foi de código/âncoras e sintaxe do módulo (rustfmt), **não** funcional.

**Observação técnica:** o produto pode chamar esse recurso de Mundo Permanente, mas disponibilizar um mundo Java multijogador pela internet exige infraestrutura de hospedagem de jogo do lado do serviço, normalmente um processo servidor Minecraft ou equivalente. A interface não precisa apresentar os detalhes técnicos.

## Etapas posteriores antes de publicar

1. Definir/contratar hospedagem sempre ativa e storage; estabelecer API de provisionamento.
2. Implementar API confiável de criar/consultar/ligar mundo, com quotas e autenticação/convites de acesso apropriados.
3. Conectar os botões a essa API (substituir o estado de rascunho pelos estados reais).
4. Testar criação, encerramento da sessão do criador, conexão externa, reconexão, backups, falhas e privacidade.
5. Integrar com a **fonte original V1.0.4** e assinatura aprovada antes de gerar APK de atualização.

Status do front-end: fonte experimental preparada; nenhuma hospedagem remota foi iniciada.
