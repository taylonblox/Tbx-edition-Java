# TBX Edition — compilação pública de testes

Este repositório público foi autorizado pelo criador do projeto TBX Edition para **compilar APKs de teste gratuitamente pelo GitHub Actions**. O projeto de desenvolvimento e os seus segredos permanecem em outro repositório privado.

**Créditos e autoria:** TBX Studio / @TheTaylonX (identidade e alterações próprias). Base técnica: Horizon Android / Horizon, por Ludovic Marie e outros colaboradores, sob licença MIT. Todos os avisos de copyright, licenças e dependências do código-fonte precisam ser respeitados. A licença de software livre permite reutilizar e modificar o código e exige a preservação dos avisos de copyright; ela não transforma um terceiro no autor original. O nome, as marcas e os elementos originais TBX Studio não devem ser falsamente reivindicados por terceiros.

## Estado da compilação — 10/11/2026

**Não utilizar o artefato `Minecraft-TBX-Edition-V1.0.5-Previa-Android` como atualização da V1.0.4.** Ele foi gerado a partir de uma reconstrução da linha V18, não do código final da V1.0.4 aprovada no Vercel Sandbox. O título interno antigo «TBX Edition V18 Preview» foi confirmado no comando Gradle do build. O workflow também não encontrou uma chave Android persistente e gerou uma chave de teste, então a atualização sem desinstalar não foi validada.

Os testes de código Android V1.0.5 concluídos com sucesso no GitHub são verificações **sem gerar APK**. Eles não comprovam equivalência à V1.0.4 nem assinatura compatível.

O workflow de APK da reconstrução antiga está **desativado para builds automáticos** e identificado como legado. Não trate a prévia antiga como lançamento oficial.

### Requisitos para uma V1.0.5 de verdade

1. Recuperar a árvore final de código que gerou a V1.0.4 aprovada (snapshot do Sandbox `tbx-android-builder`).
2. Preservar modificações da V1.0.4: visual, carregamento, shaders, controles e comportamento existente, aplicando por cima o fluxo de mods recomendados.
3. Confirmar assinatura Android original e `applicationId`; `versionCode` deve ser superior à V1.0.4.
4. Validar por teste real a instalação por cima da V1.0.4 sem desinstalar, antes de anunciar a atualização.

**Referência da V1.0.4 aprovada:** [APK original hospedado na Vercel](https://tbx-edition-v104-restore.vercel.app/Minecraft-TBX-Edition-V1.0.4-MakeUp-Restored-Android-arm64.apk). Essa APK é a última referência aprovada e não deve ser substituída por uma reconstrução V18.


Atenção: como esse código-fonte é público, outras pessoas podem copiá-lo. Evite publicar credenciais, chaves privadas, tokens ou assinaturas. Compilações com chave temporária podem exigir reinstalação no aparelho.
