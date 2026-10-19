# Tentativas Gemini excluídas do placar

Nove chamadas da primeira tentativa foram interrompidas e arquivadas aqui. O comando de lançamento foi passado ao processo Python por um *heredoc*; os `opencode run` filhos herdaram esse `stdin`, anexando o restante do script aos prompts. A exportação das nove sessões mostrou texto extra em todas; algumas também fizeram chamadas de ferramentas. Portanto, nenhum desses arquivos deve entrar na avaliação.

A reprodução de controle, com `stdin` fechado, recebeu exatamente o prompt de teste e não chamou ferramentas. A nova rodada foi lançada com `python3 -c` e entrada redirecionada de `/dev/null`; suas sessões devem ser verificadas separadamente antes da pontuação.
