def get_next_episode(content, state):
    temp = state.get("temp", 1)
    ep = state.get("ep", 1)

    temporadas = content["temporadas"]

    eps_temp = temporadas[str(temp)]

    if ep <= len(eps_temp):
        return temp, ep, eps_temp[ep-1]
    else:
        #avanza a la siguiente temporada
        temp += 1
        ep = 1
        if str(temp) in temporadas: 
            return temp, ep, temporadas[str(temp)][0]
        else:
            return None #se termina la serie

def get_next_movie(content, state):
    orden = content["orden"]
    actual = state.get("actual", orden[0])

    idx = orden.index(actual)

    if idx < len(orden):
        return orden[idx], content["archivos"][orden[idx]]
    else:
        return None
