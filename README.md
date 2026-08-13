# App Transcript

Aplicativo local e gratuito para transcrever videos e audios usando CPU/GPU da maquina.

Versao atual: `0.1.0-alpha`.

## Recursos

- Upload de varios arquivos ao mesmo tempo.
- Fila sequencial para nao sobrecarregar CPU/GPU.
- Idiomas: automatico, portugues, ingles, espanhol e frances.
- Motor `faster-whisper` com `large-v3` para maxima precisao.
- CUDA/GPU quando disponivel e fallback em CPU.
- Conversao de video/audio para MP3 local.
- O video original e apagado depois da conversao bem-sucedida.
- WAV temporario otimizado para transcricao.
- Limpeza leve automatica com FFmpeg.
- Opcao de reduzir ruido pesado com DeepFilterNet.
- Opcao de separar voz da musica com Demucs.
- Historico local em `data/jobs`.
- Player de audio sincronizado com os trechos.
- Clique em um trecho para pular o audio para aquele ponto.
- Botao "Copiar tudo".
- Carregamento inicial do modelo para evitar carregar a cada video.
- Fallback automatico para CPU se CUDA/cuBLAS/cuDNN estiver incompleto.
- Stand-by apos 20 minutos sem uso para liberar memoria.
- Modo equilibrado usa `large-v3-turbo` por padrao para notebooks.
- Modo maxima precisao continua disponivel com `large-v3`.
- Removedor de silencio inteligente com Silero VAD, fallback por energia e perfis suave/normal/agressivo.

## Como rodar como app desktop

1. Instale as dependencias Python:

```powershell
.\scripts\install.ps1
```

2. Instale as dependencias desktop:

```powershell
npm install
```

3. Abra o app:

```powershell
npm run app
```

O Electron abre uma janela propria e inicia o backend local automaticamente. Ao fechar a janela, o backend iniciado pelo app tambem e encerrado.

## Executavel e atalho

Para criar o executavel portatil:

```powershell
npm run build:launcher
```

Ele fica em:

```text
launcher\App Transcript\App Transcript.exe
```

Para criar ou recriar o atalho na Area de Trabalho:

```powershell
npm run shortcut
```

O atalho abre o app sem mostrar URL ou navegador.

Ao abrir, o app mostra uma tela de loading enquanto prepara o motor de transcricao. Esse carregamento acontece uma vez e o modelo fica reutilizavel para os videos da fila. Se a GPU for detectada mas faltar alguma DLL CUDA, o app troca para CPU automaticamente.

## Como rodar no navegador para debug

1. Instale as dependencias:

```powershell
.\scripts\install.ps1
```

2. Inicie o app:

```powershell
.\scripts\start.ps1
```

3. Abra:

```text
http://127.0.0.1:8765
```

## Audio ruim, ruido e musica

A limpeza leve fica ligada por padrao e usa filtros locais do FFmpeg. Para audio com ruido muito forte, marque "Reduzir ruido pesado". Para audio com musica de fundo, marque "Separar voz da musica".

DeepFilterNet e Demucs rodam localmente, mas sao mais pesados e podem demorar. O primeiro uso tambem pode baixar modelos gratuitos para o cache local.

## Remover silencio

A ferramenta "Remover Silencio" usa volume adaptativo para encurtar pausas longas e Silero VAD como protecao para nao cortar inicio/fim de fala. O FFmpeg renderiza o MP3 final a partir dos trechos mantidos.

Estrategias:

- Inteligente: volume adaptativo com protecao Silero. Recomendado.
- Voz Protegida: Silero como decisor principal. Melhor quando ha musica ou ruido junto da fala.
- Volume Agressivo: corta por volume com menos protecao. Melhor para narracoes e VSLs com pausas grandes.

Perfis:

- Suave: preserva mais pausas naturais.
- Normal: equilibrio recomendado.
- Agressivo: corta mais pausas e deixa o audio mais compacto.

A opcao "Preservar inicio/fim da fala" fica ativada por padrao para evitar cortar a primeira ou ultima palavra. Em audio com musica de fundo, marque "Separar voz da musica" antes do corte.

## Stand-by

Se o app ficar 20 minutos sem uso e sem transcricoes em andamento, o motor entra em stand-by para economizar CPU/GPU/RAM. O app continua aberto e o historico permanece salvo. Use "Acordar motor" ou envie uma nova transcricao para carregar o modelo novamente.

## Observacoes sobre GPU

O app tenta usar CUDA automaticamente quando o PyTorch detectar uma GPU NVIDIA compativel. Em CPU ele continua funcionando, mas arquivos longos levam mais tempo. O FFmpeg precisa estar no PATH.

Para verificar o ambiente:

```powershell
.\scripts\doctor.ps1
```

Para checar DLLs CUDA usadas pela GPU:

```powershell
.\scripts\check-gpu.ps1
```

Se faltar `cublas64_12.dll` ou `cudnn64_9.dll`, instale o runtime oficial:

```powershell
.\scripts\install-gpu-runtime.ps1
```

## Versionamento

O projeto usa versionamento semantico:

- `0.x.x-alpha`: versoes funcionais em evolucao.
- `0.x.x-beta`: versoes com recursos principais prontos e fase de polimento.
- `1.0.0`: primeira versao estavel.

Arquivos de catalogo:

- `CHANGELOG.md`: historico geral.
- `releases/vX.Y.Z/`: notas e manifesto de cada versao.

Checklist antes de catalogar uma versao:

```powershell
npm run release:check
```

Fluxo sugerido:

```powershell
git add .
git commit -m "chore: baseline App Transcript v0.1.0-alpha"
git tag v0.1.0-alpha
```
