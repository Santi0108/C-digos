"""Interfaz del juego de aventura en el castillo con Streamlit."""

import streamlit as st

from game import (
    TIEMPO_LIMITE_SEGUNDOS,
    Direccion,
    EstadoJuego,
    Juego,
    Posicion,
    TipoSala,
)

ICONOS = {
    TipoSala.TESORO: "💰",
    TipoSala.ENEMIGO: "👹",
    TipoSala.VACIA: "·",
    TipoSala.MURO: "🧱",
}

ICONO_NIEBLA = "🌫️"
TIEMPO_REFRESCO_SEGUNDOS = 1


def obtener_juego() -> Juego:
    """Devuelve la partida guardada en el estado de la sesión."""
    if "juego" not in st.session_state:
        st.session_state.juego = Juego()
        st.session_state.partida = st.session_state.get("partida", 0) + 1

    return st.session_state.juego


def mostrar_celda(juego: Juego, posicion: Posicion) -> None:
    """
    Dibuja una celda del mapa.

    Las celdas bajo la niebla de guerra solo muestran el icono de
    niebla, sin revelar su contenido.
    """
    sala = juego.castillo.sala_en(posicion)

    if not sala.revelada:
        st.markdown(f"### {ICONO_NIEBLA}")
        st.caption("Niebla")
        return

    st.markdown(f"### {ICONOS[sala.tipo]}")
    st.caption(sala.coordenadas)
    st.caption(sala.estado_texto)

    if posicion == juego.jugador.posicion and not juego.terminado:
        st.markdown("**📍 Aquí**")


def mostrar_mapa(juego: Juego) -> None:
    """Muestra el mapa completo del castillo con la niebla de guerra."""
    st.subheader("🗺️ Mapa del castillo")

    for indice_fila in range(juego.castillo.filas):
        columnas = st.columns(juego.castillo.columnas)

        for indice_columna, columna in enumerate(columnas):
            posicion = Posicion(indice_fila, indice_columna)

            with columna:
                with st.container(border=True):
                        mostrar_celda(juego, posicion)

        st.caption(
            f"{ICONO_NIEBLA} Sin explorar · 🧱 Muro · 💰 Tesoro "
            "· 👹 Enemigo · · Vacía"
        )


def mostrar_estadisticas(juego: Juego) -> None:
    """Muestra la vida, el oro, el avance y la niebla restante."""
    jugador = juego.jugador
    resueltas = len(juego.castillo.salas_resueltas)
    transitables = len(juego.castillo.salas_transitables)
    columnas = st.columns(4)

    with columnas[0]:
        st.metric("❤️ Vida", f"{jugador.vida} / {jugador.vida_maxima}")
        st.progress(jugador.vida / jugador.vida_maxima)

    with columnas[1]:
        st.metric("💰 Oro", jugador.oro)

    with columnas[2]:
        st.metric("🚪 Celdas", f"{resueltas} / {transitables}")
        st.progress(resueltas / transitables)

    with columnas[3]:
        st.metric("🌫️ Niebla", juego.castillo.niebla_restante)


def mostrar_mensaje(juego: Juego) -> None:
    """Muestra el último mensaje del juego con su color."""
    if juego.tipo_mensaje == "exito":
        st.success(juego.mensaje)
    elif juego.tipo_mensaje == "error":
        st.error(juego.mensaje)
    else:
        st.info(juego.mensaje)


def mostrar_combate(juego: Juego) -> None:
    """Muestra la operación, el reloj y el campo de respuesta."""
    sala = juego.sala_actual
    enemigo = sala.enemigo

    st.markdown(f"### ⚔️ {enemigo.nombre}")
    st.markdown(f"## {enemigo.operacion} = ?")
    st.progress(
        juego.temporizador.progreso,
        text=f"⏳ {juego.temporizador.restante:.0f} s para responder",
    )

    if sala.resuelta:
        st.caption("El combate ya terminó.")
        return

    clave = f"{st.session_state.partida}_{sala.coordenadas}"

    with st.form(f"form_combate_{clave}"):
        respuesta = st.number_input(
            "Tu respuesta",
            min_value=0,
            step=1,
            key=f"respuesta_{clave}",
        )
        enviar = st.form_submit_button(
            "⚔️ Responder", use_container_width=True
        )

    if enviar and juego.puede_responder:
        juego.responder(str(respuesta))
        st.rerun()


def mostrar_movimiento(juego: Juego) -> None:
    """
    Muestra los botones para moverse a una celda vecina.

    Los botones nunca se deshabilitan: si el jugador no puede avanzar
    en esa dirección, la niebla debe ocultarlo hasta que lo intente.
    """
    izquierda, centro, derecha = st.columns([1, 2, 1])
    deshabilitado = juego.terminado

    with centro:
        if st.button(
            Direccion.ARRIBA.value,
            key="mover_arriba",
            disabled=deshabilitado,
            use_container_width=True,
        ):
            juego.mover(Direccion.ARRIBA)
            st.rerun()

    with izquierda:
        if st.button(
            Direccion.IZQUIERDA.value,
            key="mover_izquierda",
            disabled=deshabilitado,
            use_container_width=True,
        ):
            juego.mover(Direccion.IZQUIERDA)
            st.rerun()

    with centro:
        if st.button(
            Direccion.ABAJO.value,
            key="mover_abajo",
            disabled=deshabilitado,
            use_container_width=True,
        ):
            juego.mover(Direccion.ABAJO)
            st.rerun()

    with derecha:
        if st.button(
            Direccion.DERECHA.value,
            key="mover_derecha",
            disabled=deshabilitado,
            use_container_width=True,
        ):
            juego.mover(Direccion.DERECHA)
            st.rerun()


def mostrar_resultado(juego: Juego) -> None:
    """Muestra el resumen cuando la partida termina."""
    if juego.estado == EstadoJuego.GANADO:
        st.success("🏆 ¡Ganaste! Completaste todas las celdas del castillo.")
    else:
        st.error("💀 Perdiste. Te quedaste sin puntos de vida.")

    st.metric("💰 Oro obtenido", juego.jugador.oro)
    st.info(
        "Pulsa **Reiniciar partida** en la barra lateral para "
        "jugar otra vez."
    )


@st.fragment(run_every=TIEMPO_REFRESCO_SEGUNDOS)
def panel_del_juego() -> None:
    """Dibuja el mapa, las estadísticas y los controles de la celda."""
    juego = obtener_juego()
    juego.expirar_tiempo()

    mostrar_mapa(juego)
    mostrar_estadisticas(juego)
    mostrar_mensaje(juego)

    if juego.terminado:
        mostrar_resultado(juego)
        return

    sala = juego.sala_actual
    st.subheader(f"🚪 {sala.tipo.value} · Celda {sala.coordenadas}")

    if sala.tipo == TipoSala.ENEMIGO:
        mostrar_combate(juego)

    mostrar_movimiento(juego)


def main() -> None:
    """Punto de entrada de la aplicación."""
    st.set_page_config(
        page_title="Aventura en el Castillo",
        page_icon="🏰",
        layout="wide",
    )
    juego = obtener_juego()

    st.title("🏰 Aventura en el Castillo")
    st.caption(
        "Explora el castillo entre la niebla de guerra, esquiva los muros "
        "y resuelve la operación de cada enemigo antes de que se acabe "
        "el tiempo."
    )

    with st.sidebar:
        st.header("⚔️ Partida")
        st.metric("Estado", juego.estado.value)
        st.metric("👹 Enemigos derrotados", juego.castillo.enemigos_derrotados)
        st.metric("🧱 Muros descubiertos", len(juego.castillo.muros_revelados))
        st.caption(f"Tiempo por combate: {TIEMPO_LIMITE_SEGUNDOS} s")

        if st.button("🔄 Reiniciar partida", use_container_width=True):
            juego.reiniciar()
            st.session_state.partida += 1
            st.rerun()

    panel_del_juego()


if __name__ == "__main__":
    main()