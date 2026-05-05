 Aqui está o gap analysis completo, comparando o que foi planejado no ChatGPT com o que está no repo:                                                                                                                                              
                                                                                                                                                                                                                                                    
  ---                                                                                                                                                                                                                                               
  O que está faltando no repo                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                    
  O ChatGPT planejou um sistema completo mas o que foi commitado foi apenas o esqueleto mínimo inicial. Faltam 17 arquivos e as seguintes funcionalidades:
                                                                                                                                                                                                                                                    
  Prioridade 1 — Backend (crítico, nada funciona sem isso)                                                                                                                                                                                          
                                                                                                                                                                                                                                                    
  - app/main.py só tem health check — faltam os endpoints /chat, /upload, /voice, /tts, /ws, /signup, /login                                                                                                                                        
  - app/rag.py — pipeline RAG completo com Qdrant (carregar docs, chunking, embeddings, busca vetorial)
  - app/llm.py — streaming de respostas via OpenRouter                                                                                                                                                                                              
  - app/memory.py — histórico de conversa por sessão                                                                                                                                                                                                
  - app/tts.py — text-to-speech com gTTS                                                                                                                                                                                                            
  - app/utils.py — speech-to-text com Whisper                                                                                                                                                                                                       
                                                                                                                                                                                                                                                    
  Prioridade 2 — Auth e segurança                       
                                                                                                                                                                                                                                                    
  - app/auth.py — JWT (signup, login, verify_token)                                                                                                                                                                                                 
  - app/db.py / app/models.py / app/schemas.py — PostgreSQL com SQLAlchemy
  - app/rate_limit.py — rate limiting por IP via Redis                                                                                                                                                                                              
                                                        
  Prioridade 3 — Agent com ferramentas reais                                                                                                                                                                                                        
                                                        
  - app/agent.py e app/tools.py precisam ser expandidos: hoje só fazem math ou LLM direto; falta Google Search, API caller e RAG integrado                                                                                                          
                                                        
  Prioridade 4 — Frontend                                                                                                                                                                                                                           
                                                        
  - frontend/src/App.jsx é só <h1>Chatbot UI</h1> — falta a UI de chat com WebSocket, upload de arquivos e gravação de voz                                                                                                                          
  
  Prioridade 5 — Testes e infra                                                                                                                                                                                                                     
                                                        
  - Pasta tests/ não existe — nenhum teste escrito                                                                                                                                                                                                  
  - k8s/ não existe — sem manifests Kubernetes
  - app/requirements.txt está incompleto (faltam ~15 dependências)                                                                                                                                                                                  
  - .github/workflows/deploy.yml tem o deploy como echo "deploy here"   