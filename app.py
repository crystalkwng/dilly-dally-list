import streamlit as st
import pandas as pd
from supabase import create_client
from urllib.parse import quote

st.set_page_config(page_title="The Dilly Dally List", page_icon="🧭", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1200px;}
div[data-testid="stForm"] {border: 1px solid #e6e0eb; border-radius: 14px; padding: 1rem;}
.adventure-card {padding: 1rem; border: 1px solid #e8e4eb; border-radius: 14px; margin-bottom: .75rem;}
</style>
""", unsafe_allow_html=True)

st.title("🧭 The Dilly Dally List")
st.caption("A shared home for hikes, day trips, camping ideas, and little adventures.")

# Simple shared-password gate. Store the password and database credentials in Streamlit Secrets.
if "APP_PASSWORD" not in st.secrets or "SUPABASE_URL" not in st.secrets or "SUPABASE_SERVICE_ROLE_KEY" not in st.secrets:
    st.error("Setup is not finished yet. Add APP_PASSWORD, SUPABASE_URL, and SUPABASE_SERVICE_ROLE_KEY in Streamlit Secrets.")
    st.stop()

if not st.session_state.get("signed_in", False):
    with st.form("login_form"):
        st.subheader("Welcome, dilly-dallier!")
        password = st.text_input("Shared app password", type="password")
        submitted = st.form_submit_button("Enter the list", use_container_width=True)
        if submitted:
            if password == st.secrets["APP_PASSWORD"]:
                st.session_state["signed_in"] = True
                st.rerun()
            else:
                st.error("That password didn't match. Please try again.")
    st.info("Ask the person managing the app for the shared password.")
    st.stop()

@st.cache_resource
def get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_ROLE_KEY"])

supabase = get_client()
CATEGORIES = ["Hiking", "Day trips", "Camping", "Other"]
STATUSES = ["Want to go", "Planned", "Completed"]
DIFFICULTIES = ["Easy", "Moderate", "Hard", "Very hard", "Not applicable", "Unknown"]
FIELDS = ["name", "category", "location", "distance_km", "difficulty", "status", "notes", "map_url", "latitude", "longitude"]

def load_adventures():
    result = supabase.table("adventures").select("*").order("name").execute()
    return pd.DataFrame(result.data or [])

def save_adventure(values, adventure_id=None):
    values = {k: v for k, v in values.items() if k in FIELDS}
    if adventure_id:
        supabase.table("adventures").update(values).eq("id", adventure_id).execute()
    else:
        supabase.table("adventures").insert(values).execute()

def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()

try:
    df = load_adventures()
except Exception as exc:
    st.error("I couldn't connect to the database. Check your Supabase setup and secrets.")
    st.code(str(exc))
    st.stop()

with st.sidebar:
    st.header("Find an adventure")
    search = st.text_input("Search names, places, or notes", placeholder="Try 'waterfall'...")
    categories = st.multiselect("Adventure type", CATEGORIES, default=[])
    statuses = st.multiselect("Status", STATUSES, default=[])
    difficulties = st.multiselect("Difficulty", DIFFICULTIES, default=[])
    sort_by = st.selectbox("Sort by", ["Name (A–Z)", "Name (Z–A)", "Distance (shortest)", "Distance (longest)", "Recently added"])
    st.divider()
    if st.button("↻ Refresh list", use_container_width=True):
        st.rerun()
    if st.button("Log out", use_container_width=True):
        st.session_state["signed_in"] = False
        st.rerun()

if not df.empty:
    filtered = df.copy()
    if search:
        cols = [c for c in ["name", "location", "notes", "category"] if c in filtered.columns]
        mask = filtered[cols].fillna("").astype(str).apply(lambda col: col.str.contains(search, case=False, regex=False)).any(axis=1)
        filtered = filtered[mask]
    if categories:
        filtered = filtered[filtered["category"].isin(categories)]
    if statuses:
        filtered = filtered[filtered["status"].isin(statuses)]
    if difficulties:
        filtered = filtered[filtered["difficulty"].isin(difficulties)]
    if sort_by == "Name (A–Z)":
        filtered = filtered.sort_values("name", key=lambda s: s.fillna("").str.lower())
    elif sort_by == "Name (Z–A)":
        filtered = filtered.sort_values("name", ascending=False, key=lambda s: s.fillna("").str.lower())
    elif sort_by == "Distance (shortest)":
        filtered = filtered.sort_values("distance_km", na_position="last")
    elif sort_by == "Distance (longest)":
        filtered = filtered.sort_values("distance_km", ascending=False, na_position="last")
    elif sort_by == "Recently added" and "created_at" in filtered.columns:
        filtered = filtered.sort_values("created_at", ascending=False)
else:
    filtered = df.copy()

tab_list, tab_map, tab_add, tab_import = st.tabs(["🗂️ Adventures", "🗺️ Map", "➕ Add adventure", "📥 Import list"])

with tab_list:
    total = len(df)
    shown = len(filtered)
    c1, c2, c3 = st.columns(3)
    c1.metric("All adventures", total)
    c2.metric("Showing", shown)
    c3.metric("Completed", int((df["status"] == "Completed").sum()) if not df.empty and "status" in df.columns else 0)
    st.subheader("Your adventures")
    if filtered.empty:
        st.info("No adventures match these filters yet. Add one in the 'Add adventure' tab, or clear your filters.")
    else:
        for _, row in filtered.iterrows():
            with st.container(border=True):
                top1, top2 = st.columns([4, 1])
                top1.markdown(f"### {row.get('name') or 'Untitled adventure'}")
                top1.caption(f"{row.get('category') or 'Other'}  ·  {row.get('location') or 'Location not set'}")
                top2.write(row.get("status") or "Want to go")
                details = []
                if pd.notna(row.get("distance_km")):
                    details.append(f"**Distance:** {row.get('distance_km')} km")
                if row.get("difficulty"):
                    details.append(f"**Difficulty:** {row.get('difficulty')}")
                if details:
                    st.markdown("  ·  ".join(details))
                if row.get("notes"):
                    st.write(row.get("notes"))
                if row.get("map_url"):
                    st.markdown(f"[Open map or website ↗]({row.get('map_url')})")
                elif row.get("location"):
                    query = quote(str(row.get("location")))
                    st.markdown(f"[Find on Google Maps ↗](https://www.google.com/maps/search/?api=1&query={query})")
                with st.expander("Edit this adventure"):
                    with st.form(f"edit_{row['id']}"):
                        name = st.text_input("Adventure name", value=clean_text(row.get("name", "")))
                        category = st.selectbox("Adventure type", CATEGORIES, index=CATEGORIES.index(row["category"]) if row.get("category") in CATEGORIES else 0)
                        location = st.text_input("Location", value=clean_text(row.get("location", "")))
                        distance = st.number_input("Distance (km; use 0 if not applicable)", min_value=0.0, value=float(row["distance_km"]) if pd.notna(row.get("distance_km")) else 0.0, step=0.5)
                        difficulty = st.selectbox("Difficulty", DIFFICULTIES, index=DIFFICULTIES.index(row["difficulty"]) if row.get("difficulty") in DIFFICULTIES else 5)
                        status = st.selectbox("Status", STATUSES, index=STATUSES.index(row["status"]) if row.get("status") in STATUSES else 0)
                        notes = st.text_area("Notes", value=clean_text(row.get("notes", "")))
                        map_url = st.text_input("Website or map link", value=clean_text(row.get("map_url", "")))
                        latcol, loncol = st.columns(2)
                        latitude = latcol.number_input("Latitude (optional, for map)", value=float(row["latitude"]) if pd.notna(row.get("latitude")) else 0.0, format="%.6f")
                        longitude = loncol.number_input("Longitude (optional, for map)", value=float(row["longitude"]) if pd.notna(row.get("longitude")) else 0.0, format="%.6f")
                        saved = st.form_submit_button("Save changes", use_container_width=True)
                    if saved:
                        if not name.strip():
                            st.error("Please enter an adventure name.")
                        else:
                            save_adventure({
                                "name": name.strip(), "category": category, "location": location.strip(),
                                "distance_km": distance if distance > 0 else None, "difficulty": difficulty,
                                "status": status, "notes": notes.strip(), "map_url": map_url.strip(),
                                "latitude": latitude if latitude != 0 else None,
                                "longitude": longitude if longitude != 0 else None
                            }, row["id"])
                            st.success("Adventure updated!")
                            st.rerun()
                    if st.button("Delete this adventure", key=f"delete_{row['id']}", type="secondary"):
                        st.session_state["confirm_delete"] = str(row["id"])
                    if st.session_state.get("confirm_delete") == str(row["id"]):
                        st.warning("Are you sure? This cannot be undone.")
                        yes, no = st.columns(2)
                        if yes.button("Yes, delete", key=f"yes_{row['id']}", type="primary"):
                            supabase.table("adventures").delete().eq("id", row["id"]).execute()
                            st.session_state.pop("confirm_delete", None)
                            st.rerun()
                        if no.button("Cancel", key=f"no_{row['id']}"):
                            st.session_state.pop("confirm_delete", None)
                            st.rerun()

with tab_map:
    st.subheader("Adventure map")
    st.caption("Map pins appear for adventures with latitude and longitude saved. You can add coordinates while adding or editing an adventure.")
    if not df.empty and {"latitude", "longitude"}.issubset(df.columns):
        mapped = df.dropna(subset=["latitude", "longitude"]).copy()
        mapped = mapped[(mapped["latitude"] != 0) & (mapped["longitude"] != 0)]
        if not mapped.empty:
            mapped = mapped.rename(columns={"latitude": "lat", "longitude": "lon"})
            st.map(mapped[["lat", "lon"]], size=80)
            st.dataframe(mapped[[c for c in ["name", "category", "location", "status"] if c in mapped.columns]], use_container_width=True, hide_index=True)
        else:
            st.info("No map coordinates saved yet. Add latitude and longitude to an adventure to show it here.")
            st.markdown("[Find coordinates with Google Maps](https://support.google.com/maps/answer/18539)")
    else:
        st.info("Your map will appear here once you add adventures with coordinates.")

with tab_add:
    st.subheader("Add an adventure")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("Adventure name *", placeholder="e.g. Lynn Canyon Loop")
        category = st.selectbox("Adventure type", CATEGORIES)
        location = st.text_input("Location", placeholder="e.g. North Vancouver, BC")
        col1, col2 = st.columns(2)
        distance = col1.number_input("Distance in km (0 if not applicable)", min_value=0.0, value=0.0, step=0.5)
        difficulty = col2.selectbox("Difficulty", DIFFICULTIES)
        status = st.selectbox("Status", STATUSES)
        notes = st.text_area("Notes", placeholder="Parking, best time to go, things to bring...")
        map_url = st.text_input("Website or map link", placeholder="https://...")
        st.caption("Optional: enter map coordinates to show this adventure as a pin on the map.")
        col3, col4 = st.columns(2)
        latitude = col3.number_input("Latitude", value=0.0, format="%.6f")
        longitude = col4.number_input("Longitude", value=0.0, format="%.6f")
        submitted = st.form_submit_button("Save adventure", type="primary", use_container_width=True)
    if submitted:
        if not name.strip():
            st.error("Please enter an adventure name.")
        else:
            try:
                save_adventure({
                    "name": name.strip(), "category": category, "location": location.strip(),
                    "distance_km": distance if distance > 0 else None, "difficulty": difficulty,
                    "status": status, "notes": notes.strip(), "map_url": map_url.strip(),
                    "latitude": latitude if latitude != 0 else None,
                    "longitude": longitude if longitude != 0 else None
                })
                st.success(f"Added '{name.strip()}' to The Dilly Dally List!")
                st.rerun()
            except Exception as exc:
                st.error("Could not save this adventure. Check the database setup.")
                st.code(str(exc))

with tab_import:
    st.subheader("Bring in your existing hiking list")
    st.write("Upload your Excel (.xlsx) or CSV file. The importer will show a preview and let you match your spreadsheet columns to the app fields.")
    uploaded = st.file_uploader("Choose your hiking list", type=["xlsx", "csv"])
    if uploaded:
        try:
            source = pd.read_excel(uploaded) if uploaded.name.lower().endswith(".xlsx") else pd.read_csv(uploaded)
            st.write("Preview of your file:")
            st.dataframe(source.head(10), use_container_width=True)
            source_columns = ["(skip this field)"] + list(source.columns)
            mappings = {}
            defaults = {
                "name": ["name", "trail", "adventure", "title"],
                "category": ["category", "type", "activity"],
                "location": ["location", "area", "region", "city"],
                "distance_km": ["distance_km", "distance", "length", "km"],
                "difficulty": ["difficulty", "level"],
                "status": ["status", "progress"],
                "notes": ["notes", "description", "comments"],
                "map_url": ["map_url", "url", "website", "link"]
            }
            st.write("Match your spreadsheet columns:")
            for field, label in [
                ("name", "Adventure name *"), ("category", "Adventure type"), ("location", "Location"),
                ("distance_km", "Distance (km)"), ("difficulty", "Difficulty"), ("status", "Status"),
                ("notes", "Notes"), ("map_url", "Website or map link")
            ]:
                guess = next((c for c in source.columns if str(c).strip().lower() in defaults[field]), "(skip this field)")
                ix = source_columns.index(guess) if guess in source_columns else 0
                mappings[field] = st.selectbox(label, source_columns, index=ix, key=f"map_{field}")
            if st.button("Import adventures", type="primary", use_container_width=True):
                imported = 0
                errors = []
                for _, rec in source.iterrows():
                    name_col = mappings["name"]
                    if name_col == "(skip this field)" or clean_text(rec.get(name_col, "")) == "":
                        continue
                    cat_val = clean_text(rec.get(mappings["category"], "")) if mappings["category"] != "(skip this field)" else ""
                    if cat_val not in CATEGORIES:
                        cat_val = "Hiking"
                    diff_val = clean_text(rec.get(mappings["difficulty"], "")) if mappings["difficulty"] != "(skip this field)" else ""
                    if diff_val not in DIFFICULTIES:
                        diff_val = "Unknown"
                    status_val = clean_text(rec.get(mappings["status"], "")) if mappings["status"] != "(skip this field)" else ""
                    if status_val not in STATUSES:
                        status_val = "Want to go"
                    distance_val = None
                    if mappings["distance_km"] != "(skip this field)":
                        try:
                            distance_val = float(str(rec.get(mappings["distance_km"], "")).replace(",", "."))
                            if distance_val <= 0: distance_val = None
                        except Exception:
                            distance_val = None
                    values = {
                        "name": clean_text(rec.get(name_col, "")), "category": cat_val,
                        "location": clean_text(rec.get(mappings["location"], "")) if mappings["location"] != "(skip this field)" else "",
                        "distance_km": distance_val, "difficulty": diff_val, "status": status_val,
                        "notes": clean_text(rec.get(mappings["notes"], "")) if mappings["notes"] != "(skip this field)" else "",
                        "map_url": clean_text(rec.get(mappings["map_url"], "")) if mappings["map_url"] != "(skip this field)" else ""
                    }
                    try:
                        save_adventure(values)
                        imported += 1
                    except Exception as exc:
                        errors.append(f"{values['name']}: {exc}")
                st.success(f"Imported {imported} adventures.")
                if errors:
                    st.warning(f"{len(errors)} rows could not be imported.")
                    st.code("\n".join(errors[:5]))
                st.rerun()
        except Exception as exc:
            st.error("I could not read that file. Please check that it is a valid Excel or CSV file.")
            st.code(str(exc))

st.divider()
st.caption("Made for spontaneous plans and happy detours. Keep your shared password private.")
