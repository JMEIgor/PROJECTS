v_cdr
- uniqueid => identificador da ligação
- horario => data/hora da ligação
- origem => número de origem (pode ser ramal ou externo)
- destino => número de destino (pode ser ramal, externo, ura ou fila)
- duracao => tempo em segundos
- tipo => tipo da ligação E => entrada, S => Saída, I => Interna
- tipo_numero => para ligações de saída, o tipo de serviço DDD, MOVEL, LOCAL
Essa tabela você pode usar para tratar as ligações de saída, as ligações de entrada você pode centralizar na v_queue_calls_full, pois tem mais informação e menos duplicidade