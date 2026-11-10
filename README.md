# TBX Edition — compilação pública de testes

Este repositório público foi autorizado pelo criador do projeto TBX Edition para **compilar APKs de teste gratuitamente pelo GitHub Actions**. O projeto de desenvolvimento e os seus segredos permanecem em outro repositório privado.

**Créditos e autoria:** TBX Studio / @TheTaylonX (identidade e alterações próprias). Base técnica: Horizon Android / Horizon, por Ludovic Marie e outros colaboradores, sob licença MIT. Todos os avisos de copyright, licenças e dependências do código-fonte precisam ser respeitados. A licença de software livre permite reutilizar e modificar o código e exige a preservação dos avisos de copyright; ela não transforma um terceiro no autor original. O nome, as marcas e os elementos originais TBX Studio não devem ser falsamente reivindicados por terceiros.

## Próximo APK

1. Abra **Actions**.
2. Selecione **TBX Edition - Compilar APK Android (Prévia Conversor)**.
3. Entre na execução e acompanhe o progresso; pode fechar a aba.
4. Quando a execução terminar com sucesso, baixe o arquivo na seção **Artifacts**.

O workflow também é iniciado automaticamente após a publicação desta configuração.

**Limitações:** esta fonte é uma base anterior à V1.0.4. A engrenagem da HUD touch foi removida do código, mas isso ainda precisa ser confirmado no APK. O Superconversor Rust/Python está em fase experimental; os utilitários de conversão que existem no repositório não provam que arquivos Java `.jar` funcionarão dentro do jogo ou que há interface pronta no APK.

O código-fonte revisado para CI, incluindo avisos de licença e créditos: https://tbx-public-source-ci.vercel.app/

Atenção: como esse código-fonte é público, outras pessoas podem copiá-lo. Evite publicar credenciais, chaves privadas, tokens ou assinaturas. Compilações com chave temporária podem exigir reinstalação no aparelho.
