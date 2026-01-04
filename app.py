import streamlit as st
from core.repositories import SqliteRepos
from core.policies import StudentPolicy, MentorPolicy
from core.storage import LocalImageStorage
from core.services import ArtConnectService

st.set_page_config(page_title="ArtConnect", layout="wide")

repos = SqliteRepos()
storage = LocalImageStorage()

def policy_for(role: str):
    return MentorPolicy() if role == "mentor" else StudentPolicy()

def service():
    role = st.session_state.get("role", "student")
    return ArtConnectService(repos, storage, policy_for(role))

if "uid" not in st.session_state:
    st.session_state.uid = None
    st.session_state.role = None

st.sidebar.title("ArtConnect")

if not st.session_state.uid:
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            res = service().login(u, p)
            if res:
                st.session_state.uid, st.session_state.role = res
                st.rerun()
            else:
                st.error("Krivi username ili password.")

    with tab2:
        u = st.text_input("Novi username", key="ru")
        p = st.text_input("Novi password", type="password", key="rp")
        r = st.selectbox("Rola", ["student", "mentor"])
        if st.button("Register"):
            try:
                service().register(u, p, r)
                st.success("Korisnik kreiran. Sad se logiraj.")
            except Exception:
                st.error("Username već postoji (ili greška).")

    st.stop()

st.sidebar.success(f"Ulogiran: {st.session_state.role}")
if st.sidebar.button("Logout"):
    st.session_state.uid = None
    st.session_state.role = None
    st.rerun()

page = st.sidebar.radio("Navigacija", ["Izložbe", "Nova izložba (mentor)"])

st.title("Virtualne izložbe")

if page == "Nova izložba (mentor)":
    if st.session_state.role != "mentor":
        st.info("Samo mentor može kreirati izložbu.")
    else:
        theme = st.text_input("Tema")
        desc = st.text_area("Opis")
        if st.button("Kreiraj izložbu"):
            service().create_exhibition(theme, desc, st.session_state.uid)
            st.success("Kreirano.")
            st.rerun()

exhibitions = repos.list_exhibitions()
if not exhibitions:
    st.info("Još nema izložbi.")
    st.stop()

exh = st.selectbox("Odaberi izložbu", exhibitions, format_func=lambda e: f"#{e.id} — {e.theme}")
st.subheader(exh.theme)
st.write(exh.description)
if st.session_state.role == "mentor":
    st.warning("Ova akcija briše izložbu, sve slike i sve komentare.")
    if st.button("🗑️ Obriši izložbu"):
        repos.delete_exhibition(exh.id)
        st.success("Izložba obrisana.")
        st.rerun()


st.caption(f"Broj radova: {len(repos.list_artworks(exh.id))}")

if st.session_state.role == "mentor":
    up = st.file_uploader("Upload rada (slika)", type=["png", "jpg", "jpeg"])
    if up and st.button("Spremi rad"):
        try:
            service().upload_artwork(exh.id, up, st.session_state.uid)
            st.success("Uploadano.")
            st.rerun()
        except Exception as e:
            st.error(str(e))

st.divider()
artworks = repos.list_artworks(exh.id)

for a in artworks:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.image(a.path, caption=a.filename, use_container_width=True)
    with col2:        
        likes = repos.like_count(a.id)
        if st.session_state.role == "mentor":
            if st.button("🗑️ Obriši sliku", key=f"del_art_{a.id}"):
                repos.delete_artwork(a.id)
                st.rerun()

        if st.button(f"❤️ Like ({likes})", key=f"like_{a.id}"):
            repos.toggle_like(st.session_state.uid, a.id)
            st.rerun()

        c = st.text_input("Komentar", key=f"c_{a.id}")
        if st.button("Dodaj komentar", key=f"addc_{a.id}"):
            if c.strip():
                repos.add_comment(st.session_state.uid, a.id, c.strip())
                st.rerun()

        st.write("**Komentari:**")
        for cid, user, text in repos.list_comments(a.id)[:5]:
            colc1, colc2 = st.columns([10, 1])
            with colc1:
                st.write(f"- **{user}**: {text}")
            with colc2:
                if st.session_state.role == "mentor":
                    if st.button("🗑️", key=f"del_c_{cid}"):
                        repos.delete_comment(cid)
                        st.rerun()