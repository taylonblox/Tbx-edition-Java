# TBX Hybrid Preview — primeira implementação pública

Esta branch cria um teste ARM64 separado, a partir do Starling 0.8.0
(commit ac874422ed8f892505ff73d67ae486ecfee7a516, licença MIT).
Aplica o overlay azul TBX e remove a engrenagem extra do HUD. O aplicativo
experimental tem ID dev.tbx.hybrid.preview e nome TBX Hybrid Preview;
não utiliza a assinatura nem o ID da TBX Edition V1.0.4.

## Java e mods
Inclui uma classe Android/Java 8 que inspeciona arquivos ZIP/JAR e reconhece
metadados Fabric, Forge, NeoForge, Quilt, resource packs e shader packs.
O arquivo é identificado com checagem de caminhos perigosos, mas não é
executado. Ainda não existe menu ligado ao inspetor.
Mods Java JAR *não rodam* neste APK; executar mods Java exige JVM e motor Java
compatíveis. A conversão nativa do Starling preserva apenas alguns dados, não
os comportamentos Java.

## APK
A action TBX Hybrid Preview - Android ARM64 testa a classe Java e tenta
compilar um APK experimental com o motor Rust existente. Consulte o estado
da execução em Actions e baixe o artefato apenas após sucesso.
Requer Minecraft legalmente obtido para preparar seus próprios arquivos;
não distribui recursos da Mojang. Uma assinatura temporária de CI pode
exigir instalação limpa em futuras prévias.

ESTE APK NÃO É UMA ATUALIZAÇÃO da V1.0.4 aprovada, cujo estado final de
código e assinatura ainda precisam ser recuperados. Não substituir 1.0.4.

Créditos: Starling/Horizon e seus contribuidores, LICENSE MIT e avisos
preservados no artefato. Overlay TBX Studio / @TheTaylonX. Projeto não oficial.
