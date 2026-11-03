def get_next_episode(content, state):
    temp = state.get("temp", 1)
    ep = state.get("ep", 1)

    temporadas = content["temporadas"]

    while str(temp) in temporadas:
        eps_temp = temporadas[str(temp)]

        if ep <= len(eps_temp):
            return temp, ep, eps_temp[ep - 1]

        temp += 1
        ep = 1

    return None


def get_next_movie(content, state):
    orden = content["orden"]
    actual = state.get("actual", orden[0])

    if actual not in orden:
        return None

    idx = orden.index(actual)

    if idx < len(orden):
        return orden[idx], content["archivos"][orden[idx]]

    return None
