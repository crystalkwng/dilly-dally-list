import streamlit as st
import pandas as pd
import uuid
from supabase import create_client
from urllib.parse import quote

st.set_page_config(page_title="The Dilly Dally List", page_icon="🧭", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:opsz,wght@9..144,600;9..144,700;9..144,800&display=swap');
:root { --cream:#fff7e7; --paper:#fffdf7; --ink:#243c36; --tomato:#d95e3f; --gold:#e9b949; --sage:#8b9c68; --pink:#e7a28d; }
.stApp { background: #fff8eb; color: var(--ink); }
.block-container {padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1240px;}
[data-testid="stSidebar"] {background: #e9edda; border-right: 2px solid #d9dfc6;}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] label {color:#243c36;}
h1, h2, h3 {font-family:'Fraunces', Georgia, serif !important; color:#243c36; letter-spacing:-.035em;}
p, label, div, span {font-family:'DM Mono', 'Trebuchet MS', sans-serif;}
[data-testid="stMetric"] {background:#fffdf7; border:2px solid #243c36; border-radius:16px; padding:15px 18px; box-shadow:4px 4px 0 #e9b949;}
[data-testid="stMetricLabel"] {color:#5b6b4d; font-size:.8rem; text-transform:uppercase; letter-spacing:.08em;}
[data-testid="stMetricValue"] {color:#d95e3f; font-family:'Fraunces',Georgia,serif;}
[data-testid="stTabs"] button {font-family:'DM Mono',monospace; font-weight:600; border-radius:999px; padding:.55rem 1rem;}
[data-testid="stTabs"] button[aria-selected="true"] {background:#243c36; color:#fff7e7;}
.stButton button, [data-testid="stFormSubmitButton"] button {border:2px solid #243c36; border-radius:999px; font-weight:700; box-shadow:3px 3px 0 #e9b949; transition:transform .15s ease;}
.stButton button:hover, [data-testid="stFormSubmitButton"] button:hover {transform:translate(-1px,-1px); border-color:#243c36; box-shadow:4px 4px 0 #d95e3f;}
[data-testid="stForm"] {background:#fffdf7; border:2px solid #d9dfc6; border-radius:18px; padding:1.1rem;}
[data-testid="stExpander"] {background:#fffdf7; border:1px solid #d9dfc6; border-radius:12px;}
input, textarea, [data-baseweb="select"] > div {border-radius:10px !important;}
.dd-hero {background:#f2c85b; border:3px solid #243c36; border-radius:24px; padding:1.35rem 1.5rem; margin:.1rem 0 1.2rem; box-shadow:7px 7px 0 #d95e3f; position:relative; overflow:hidden;}
.dd-hero h1 {font-size:clamp(2.2rem,5vw,4.1rem); line-height:.98; margin:.2rem 0 .55rem; color:#243c36;}
.dd-hero p {margin:0; max-width:620px; font-size:.94rem; line-height:1.65; color:#243c36;}
.dd-kicker {text-transform:uppercase; letter-spacing:.16em; font-size:.72rem; font-weight:700; color:#d95e3f;}
.dd-sticker {display:inline-block; border:2px solid #243c36; border-radius:999px; background:#fff7e7; padding:.28rem .65rem; margin:.7rem .25rem 0 0; font-family:'DM Mono',monospace; font-size:.7rem; font-weight:700; transform:rotate(-2deg);}
.dd-section {font-family:'Fraunces',Georgia,serif; font-size:1.65rem; font-weight:800; color:#243c36; margin:.25rem 0 .7rem;}
.dd-note {background:#e9edda; border-left:5px solid #8b9c68; padding:.8rem 1rem; border-radius:0 12px 12px 0; color:#243c36;}
@media (max-width: 700px) { .block-container {padding-left:1rem; padding-right:1rem;} .dd-hero {padding:1.1rem;} }
</style>
<div class="dd-hero">
  <div class="dd-kicker">✳ wandering aimelessly ✳</div>
  <h1>The Dilly Dally List</h1>
  <p>Don't adventures ever have an end? I suppose not. - Bilbo Baggins</p>
  <span class="dd-sticker">✿ JUST DILLY DALLYING</span><span class="dd-sticker">★ OUT THERE SOMEWHERE</span>
</div>
""", unsafe_allow_html=True)

# Simple shared-password gate. Store the password and database credentials in Streamlit Secrets.
if "APP_PASSWORD" not in st.secrets or "SUPABASE_URL" not in st.secrets or "SUPABASE_SERVICE_ROLE_KEY" not in st.secrets:
    st.error("Setup is not finished yet. Add APP_PASSWORD, SUPABASE_URL, and SUPABASE_SERVICE_ROLE_KEY in Streamlit Secrets.")
    st.stop()

if not st.session_state.get("signed_in", False):
    with st.form("login_form"):
        st.subheader("Where to next? ✿")
        password = st.text_input("Password please", type="password")
        submitted = st.form_submit_button("Enter the list", use_container_width=True)
        if submitted:
            if password == st.secrets["APP_PASSWORD"]:
                st.session_state["signed_in"] = True
                st.rerun()
            else:
                st.error("Error, wrong password. It's not that hard.")
    st.markdown("<div class='dd-note'>🌼 no password, no bueno.</div>", unsafe_allow_html=True)
    st.stop()

@st.cache_resource
def get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_ROLE_KEY"])

supabase = get_client()
CATEGORIES = ["Hiking", "Day trips", "Road trips", "Camping", "Biking", "Other"]
STATUSES = ["Want to go", "Planned", "Completed"]
DIFFICULTIES = ["Easy", "Moderate", "Hard", "Strenuous", "Not applicable", "Unknown"]
FIELDS = ["name", "category", "location", "distance_km", "elevation_gain_m", "difficulty", "status", "notes", "map_url", "latitude", "longitude", "photo_url"]
CATEGORY_ART = {
    "Hiking": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=700&q=85",
    "Day trips": "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?auto=format&fit=crop&w=700&q=85",
    "Camping": "https://images.unsplash.com/photo-1478131143081-80f7f84ca84d?auto=format&fit=crop&w=700&q=85",
    "Road trips": "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=700&q=85",
    "Biking": "https://images.unsplash.com/photo-1544191696-15693072b35a?auto=format&fit=crop&w=700&q=85",
    "Other": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=700&q=85",
}
CATEGORY_EMOJI = {"Hiking": "🥾", "Day trips": "🚙", "Road trips": "🚗", "Camping": "🏕️", "Biking": "🚲", "Other": "🌼"}

def load_adventures():
    result = supabase.table("adventures").select("*").order("name").execute()
    return pd.DataFrame(result.data or [])

def save_adventure(values, adventure_id=None):
    values = {k: v for k, v in values.items() if k in FIELDS}
    if adventure_id:
        supabase.table("adventures").update(values).eq("id", adventure_id).execute()
    else:
        supabase.table("adventures").insert(values).execute()

def upload_adventure_photo(uploaded_file):
    """Upload an image to Supabase Storage and return its public URL."""
    if uploaded_file is None:
        return None

    extension = uploaded_file.name.rsplit(".", 1)[-1].lower() if "." in uploaded_file.name else ""
    allowed_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
    }
    if extension not in allowed_types:
        raise ValueError("Please upload a JPG, PNG, WEBP, or GIF image.")

    # Keep uploads reasonably sized for a phone-friendly app.
    if uploaded_file.size > 10 * 1024 * 1024:
        raise ValueError("Please choose an image smaller than 10 MB.")

    path = f"{uuid.uuid4().hex}.{extension}"
    supabase.storage.from_("adventure-photos").upload(
        path,
        uploaded_file.getvalue(),
        file_options={"content-type": allowed_types[extension], "upsert": "false"},
    )
    return supabase.storage.from_("adventure-photos").get_public_url(path)

ATTACHMENT_BUCKET = "adventure-attachments"
ATTACHMENT_TYPES = [
    "gpx", "pdf", "doc", "docx", "xls", "xlsx", "csv", "txt",
    "jpg", "jpeg", "png", "webp", "zip", "kml", "kmz", "tcx",
    "geojson", "fit", "gpx.gz",
]

def upload_adventure_attachment(adventure_id, uploaded_file):
    """Upload an attachment and save its metadata against an adventure."""
    if uploaded_file is None:
        return
    if uploaded_file.size > 25 * 1024 * 1024:
        raise ValueError("Please choose a file smaller than 25 MB.")

    original_name = uploaded_file.name.replace("\\", "/").split("/")[-1].strip() or "attachment"
    safe_name = "".join(ch if ch.isalnum() or ch in "._- " else "_" for ch in original_name).strip() or "attachment"
    path = f"{uuid.uuid4().hex}_{safe_name}"
    content_type = uploaded_file.type or "application/octet-stream"

    supabase.storage.from_(ATTACHMENT_BUCKET).upload(
        path, uploaded_file.getvalue(),
        file_options={"content-type": content_type, "upsert": "false"},
    )
    public_url = supabase.storage.from_(ATTACHMENT_BUCKET).get_public_url(path)
    supabase.table("adventure_attachments").insert({
        "adventure_id": str(adventure_id),
        "file_name": original_name,
        "storage_path": path,
        "public_url": public_url,
        "content_type": content_type,
        "file_size": uploaded_file.size,
    }).execute()

def delete_adventure_attachment(attachment):
    """Delete a stored file and its metadata row."""
    supabase.storage.from_(ATTACHMENT_BUCKET).remove([attachment["storage_path"]])
    supabase.table("adventure_attachments").delete().eq("id", attachment["id"]).execute()

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

try:
    attachment_result = supabase.table("adventure_attachments").select("*").order("created_at", desc=True).execute()
    attachments_df = pd.DataFrame(attachment_result.data or [])
    attachments_table_ready = True
    attachments_setup_error = ""
except Exception as exc:
    attachments_df = pd.DataFrame()
    attachments_table_ready = False
    attachments_setup_error = str(exc)

with st.sidebar:
    st.header("Where to next?")
    search = st.text_input("Search names, places, or notes", placeholder="Try 'waterfall'...")
    categories = st.multiselect("Adventure type", CATEGORIES, default=[])
    statuses = st.multiselect("Status", STATUSES, default=[])
    difficulties = st.multiselect("Difficulty", DIFFICULTIES, default=[])
    sort_by = st.selectbox("Sort by", ["Name (A–Z)", "Name (Z–A)", "Distance (shortest)", "Distance (longest)", "Elevation gain (lowest)", "Elevation gain (highest)", "Recently added"])
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
    elif sort_by == "Elevation gain (lowest)":
        if "elevation_gain_m" in filtered.columns:
            filtered = filtered.sort_values("elevation_gain_m", na_position="last")
    elif sort_by == "Elevation gain (highest)":
        if "elevation_gain_m" in filtered.columns:
            filtered = filtered.sort_values("elevation_gain_m", ascending=False, na_position="last")
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
    st.markdown("<div class='dd-section'>✿ What's the next adventure?</div>", unsafe_allow_html=True)
    if filtered.empty:
        st.info("No adventures match these filters yet. Add one in the 'Add adventure' tab, or clear your filters.")
    else:
        for _, row in filtered.iterrows():
            with st.container(border=True):
                picture, content = st.columns([1, 3], gap="medium")
                category_name = row.get("category") or "Other"
                custom_photo = clean_text(row.get("photo_url", ""))
                picture.image(custom_photo or CATEGORY_ART.get(category_name, CATEGORY_ART["Other"]), use_container_width=True)
                picture.caption(f"{CATEGORY_EMOJI.get(category_name, '🌼')} {category_name.upper()}")
                top1, top2 = content.columns([4, 1])
                top1.markdown(f"### {row.get('name') or 'Untitled adventure'}")
                top1.caption(f"📍 {row.get('location') or 'Location not set'}")
                status_value = row.get("status") or "Want to go"
                status_icon = {"Want to go": "✦", "Planned": "◷", "Completed": "✓"}.get(status_value, "✦")
                top2.markdown(f"**{status_icon} {status_value}**")
                details = []
                if pd.notna(row.get("distance_km")):
                    details.append(f"🥾 {row.get('distance_km')} km")
                if pd.notna(row.get("elevation_gain_m")):
                    details.append(f"↗ {float(row.get('elevation_gain_m')):g} m elevation gain")
                if row.get("difficulty"):
                    details.append(f"⛰️ {row.get('difficulty')}")
                if details:
                    content.markdown(" · ".join(details))
                if row.get("notes"):
                    content.markdown(f"<div class='dd-note'>✿ {row.get('notes')}</div>", unsafe_allow_html=True)
                if row.get("map_url"):
                    content.markdown(f"[The Finer Details ↗]({row.get('map_url')})")
                elif row.get("location"):
                    query = quote(str(row.get("location")))
                    content.markdown(f"[Find on Google Maps ↗](https://www.google.com/maps/search/?api=1&query={query})")
                lat_value = pd.to_numeric(pd.Series([row.get("latitude")]), errors="coerce").iloc[0]
                lon_value = pd.to_numeric(pd.Series([row.get("longitude")]), errors="coerce").iloc[0]
                if pd.notna(lat_value) and pd.notna(lon_value) and lat_value != 0 and lon_value != 0:
                    directions_url = f"https://www.google.com/maps/dir/?api=1&destination={lat_value:.6f}%2C{lon_value:.6f}&travelmode=driving"
                    content.markdown(f"[🚗 Directions↗]({directions_url})")
                with st.expander("📎 Important files & info", expanded=False):
                    st.caption("GPX routes, PDFs, packing lists, permits, etc. Maximum upload size: 25 MB per file.")
                    if not attachments_table_ready:
                        st.warning("Attachments need a one-time Supabase setup before they can be used. Run the add_adventure_attachments.sql file included in this project ZIP in Supabase SQL Editor, then refresh this app.")
                    else:
                        adventure_attachments = attachments_df[attachments_df["adventure_id"].astype(str) == str(row["id"])] if not attachments_df.empty and "adventure_id" in attachments_df.columns else pd.DataFrame()
                        if adventure_attachments.empty:
                            st.info("No files attached to this adventure yet.")
                        else:
                            for _, attachment in adventure_attachments.iterrows():
                                file_col, remove_col = st.columns([5, 1])
                                size_bytes = pd.to_numeric(pd.Series([attachment.get("file_size")]), errors="coerce").iloc[0]
                                size_label = f" · {size_bytes / 1024:.0f} KB" if pd.notna(size_bytes) else ""
                                file_col.markdown(f"📄 [{attachment.get('file_name', 'Download attachment')}]({attachment.get('public_url', '')}){size_label}")
                                if remove_col.button("Remove", key=f"remove_attachment_{attachment['id']}"):
                                    try:
                                        delete_adventure_attachment(attachment.to_dict())
                                        st.success("Attachment removed.")
                                        st.rerun()
                                    except Exception as exc:
                                        st.error("Could not remove this attachment.")
                                        st.code(str(exc))
                        new_attachment = st.file_uploader(
                            "Add a file",
                            type=ATTACHMENT_TYPES,
                            key=f"attachment_upload_{row['id']}",
                            help="Supported examples: GPX, PDF, Word, Excel, CSV, text, ZIP, etc.",
                        )
                        if st.button("Upload attachment", key=f"upload_attachment_{row['id']}", use_container_width=True, disabled=new_attachment is None):
                            try:
                                upload_adventure_attachment(row["id"], new_attachment)
                                st.success("File uploaded and saved with this adventure!")
                                st.rerun()
                            except Exception as exc:
                                st.error("Could not upload this file. Check that the attachment bucket and table are set up.")
                                st.code(str(exc))

                action_col, spacer_col = content.columns([1, 5])
                if action_col.button("✎ Edit adventure", key=f"edit_toggle_{row['id']}", use_container_width=True):
                    current_edit = st.session_state.get("editing_adventure")
                    if current_edit == str(row["id"]):
                        st.session_state.pop("editing_adventure", None)
                    else:
                        st.session_state["editing_adventure"] = str(row["id"])
                    st.rerun()

                if st.session_state.get("editing_adventure") == str(row["id"]):
                    st.markdown("#### ✎ Edit your adventure")
                    st.caption("Make your changes below, then save. Your shared list will update for everyone.")
                    with st.form(f"edit_{row['id']}"):
                        name = st.text_input("Adventure name", value=clean_text(row.get("name", "")))
                        category = st.selectbox("Adventure type", CATEGORIES, index=CATEGORIES.index(row["category"]) if row.get("category") in CATEGORIES else 0)
                        location = st.text_input("Location", value=clean_text(row.get("location", "")))
                        distance = st.number_input("Distance (km; use 0 if not applicable)", min_value=0.0, value=float(row["distance_km"]) if pd.notna(row.get("distance_km")) else 0.0, step=0.5)
                        elevation_gain = st.number_input("Elevation gain (metres; 0 if unknown)", min_value=0, value=int(float(row["elevation_gain_m"])) if pd.notna(row.get("elevation_gain_m")) else 0, step=25)
                        difficulty = st.selectbox("Difficulty", DIFFICULTIES, index=DIFFICULTIES.index(row["difficulty"]) if row.get("difficulty") in DIFFICULTIES else 5)
                        status = st.selectbox("Status", STATUSES, index=STATUSES.index(row["status"]) if row.get("status") in STATUSES else 0)
                        notes = st.text_area("Notes", value=clean_text(row.get("notes", "")))
                        map_url = st.text_input("Website or map link", value=clean_text(row.get("map_url", "")))
                        photo_url = st.text_input(
                            "Photo URL (optional)",
                            value=clean_text(row.get("photo_url", "")),
                            help="Paste a direct link to an image, or upload a replacement below.",
                            key=f"edit_photo_url_{row['id']}",
                        )
                        uploaded_photo = st.file_uploader(
                            "Upload a replacement photo (optional)",
                            type=["jpg", "jpeg", "png", "webp", "gif"],
                            key=f"edit_photo_file_{row['id']}",
                        )
                        clear_photo = st.checkbox("Remove custom photo and use the category picture", key=f"clear_photo_{row['id']}")
                        latcol, loncol = st.columns(2)
                        latitude = latcol.number_input("Latitude (optional, for map)", value=float(row["latitude"]) if pd.notna(row.get("latitude")) else 0.0, format="%.6f")
                        longitude = loncol.number_input("Longitude (optional, for map)", value=float(row["longitude"]) if pd.notna(row.get("longitude")) else 0.0, format="%.6f")
                        saved = st.form_submit_button("Save changes", use_container_width=True)
                    cancel_col, _ = st.columns([1, 5])
                    if cancel_col.button("Cancel editing", key=f"cancel_edit_{row['id']}"):
                        st.session_state.pop("editing_adventure", None)
                        st.rerun()
                    if saved:
                        if not name.strip():
                            st.error("Please enter an adventure name.")
                        else:
                            try:
                                chosen_photo_url = photo_url.strip() or None
                                if clear_photo:
                                    chosen_photo_url = None
                                elif uploaded_photo is not None:
                                    chosen_photo_url = upload_adventure_photo(uploaded_photo)

                                save_adventure({
                                    "name": name.strip(), "category": category, "location": location.strip(),
                                    "distance_km": distance if distance > 0 else None, "elevation_gain_m": elevation_gain if elevation_gain > 0 else None, "difficulty": difficulty,
                                    "status": status, "notes": notes.strip(), "map_url": map_url.strip(),
                                    "latitude": latitude if latitude != 0 else None,
                                    "longitude": longitude if longitude != 0 else None,
                                    "photo_url": chosen_photo_url,
                                }, row["id"])
                                st.session_state.pop("editing_adventure", None)
                                st.success("Adventure updated!")
                                st.rerun()
                            except Exception as exc:
                                st.error("Could not save the adventure or upload its photo. Check that the photo bucket is set up.")
                                st.code(str(exc))

                if st.button("🗑 Delete adventure", key=f"delete_{row['id']}", type="secondary"):
                    st.session_state["confirm_delete"] = str(row["id"])
                if st.session_state.get("confirm_delete") == str(row["id"]):
                    st.warning("Are you sure? This cannot be undone.")
                    yes, no = st.columns(2)
                    if yes.button("Yes, delete", key=f"yes_{row['id']}", type="primary"):
                        # Remove this adventure's attachments from Storage and metadata first.
                        if attachments_table_ready and not attachments_df.empty and "adventure_id" in attachments_df.columns:
                            related_attachments = attachments_df[attachments_df["adventure_id"].astype(str) == str(row["id"])]
                            for _, attachment in related_attachments.iterrows():
                                try:
                                    delete_adventure_attachment(attachment.to_dict())
                                except Exception:
                                    pass
                        supabase.table("adventures").delete().eq("id", row["id"]).execute()
                        st.session_state.pop("confirm_delete", None)
                        if st.session_state.get("editing_adventure") == str(row["id"]):
                            st.session_state.pop("editing_adventure", None)
                        st.rerun()
                    if no.button("Cancel", key=f"no_{row['id']}"):
                        st.session_state.pop("confirm_delete", None)
                        st.rerun()

with tab_map:
    st.markdown("<div class='dd-section'>✹ Wandering about</div>", unsafe_allow_html=True)
    st.caption("Click to see adventure’s details")
    if not df.empty and {"latitude", "longitude"}.issubset(df.columns):
        mapped = df.copy()
        mapped["latitude"] = pd.to_numeric(mapped["latitude"], errors="coerce")
        mapped["longitude"] = pd.to_numeric(mapped["longitude"], errors="coerce")
        mapped = mapped.dropna(subset=["latitude", "longitude"])
        mapped = mapped[(mapped["latitude"] != 0) & (mapped["longitude"] != 0)]
        if not mapped.empty:
            map_data = pd.DataFrame({
                "adventure_id": mapped["id"].astype(str),
                "name": mapped["name"].fillna("Untitled adventure").astype(str),
                "location": mapped["location"].fillna("").astype(str) if "location" in mapped.columns else "",
                "category": mapped["category"].fillna("Other").astype(str) if "category" in mapped.columns else "Other",
                "status": mapped["status"].fillna("Want to go").astype(str) if "status" in mapped.columns else "Want to go",
                "lat": mapped["latitude"],
                "lon": mapped["longitude"],
            })
            import pydeck as pdk

            view_state = pdk.ViewState(
                latitude=float(map_data["lat"].mean()),
                longitude=float(map_data["lon"].mean()),
                zoom=7 if len(map_data) > 1 else 10,
                pitch=0,
            )
            pin_layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_data,
                get_position="[lon, lat]",
                get_radius=180,
                radius_min_pixels=7,
                radius_max_pixels=18,
                get_fill_color=[217, 94, 63, 220],
                get_line_color=[36, 60, 54, 255],
                line_width_min_pixels=2,
                stroked=True,
                pickable=True,
                auto_highlight=True,
                id="adventure-pins",
            )
            deck = pdk.Deck(
                layers=[pin_layer],
                initial_view_state=view_state,
                tooltip={"html": "<b>{name}</b><br/>{location}<br/>{category} · {status}", "style": {"backgroundColor": "#fffdf7", "color": "#243c36"}},
                map_style="light",
            )
            map_event = st.pydeck_chart(
                deck,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-object",
                key="adventure_map",
            )
            # Save the clicked pin's ID so its details remain visible after Streamlit reruns.
            try:
                selection = map_event.selection
                selected_objects = selection.get("objects", {}) if hasattr(selection, "get") else {}
                for layer_objects in selected_objects.values():
                    if layer_objects:
                        clicked_id = str(layer_objects[0].get("adventure_id", ""))
                        if clicked_id:
                            st.session_state["selected_map_adventure_id"] = clicked_id
                        break
            except (AttributeError, TypeError, KeyError, IndexError):
                pass

            selected_id = st.session_state.get("selected_map_adventure_id")
            selected_rows = mapped[mapped["id"].astype(str) == str(selected_id)] if selected_id else mapped.iloc[0:0]
            if not selected_rows.empty:
                selected_row = selected_rows.iloc[0]
                st.markdown("### ✦ Selected adventure")
                selected_photo = clean_text(selected_row.get("photo_url", ""))
                if selected_photo:
                    st.image(selected_photo, width=320)
                st.subheader(clean_text(selected_row.get("name", "")) or "Untitled adventure")
                if clean_text(selected_row.get("location", "")):
                    st.caption(f"📍 {clean_text(selected_row.get('location', ''))}")
                selected_details = []
                if pd.notna(selected_row.get("distance_km")):
                    selected_details.append(f"🥾 {selected_row.get('distance_km')} km")
                if pd.notna(selected_row.get("elevation_gain_m")):
                    selected_details.append(f"↗ {float(selected_row.get('elevation_gain_m')):g} m elevation gain")
                if clean_text(selected_row.get("difficulty", "")):
                    selected_details.append(f"⛰️ {clean_text(selected_row.get('difficulty', ''))}")
                if selected_details:
                    st.write(" · ".join(selected_details))
                if clean_text(selected_row.get("notes", "")):
                    st.markdown(f"<div class='dd-note'>✿ {clean_text(selected_row.get('notes', ''))}</div>", unsafe_allow_html=True)
                directions_url = f"https://www.google.com/maps/dir/?api=1&destination={float(selected_row['latitude']):.6f}%2C{float(selected_row['longitude']):.6f}&travelmode=driving"
                st.markdown(f"[🚗 Directions↗]({directions_url})")
                if st.button("✎ Edit this adventure", key=f"map_edit_{selected_id}"):
                    st.session_state["editing_adventure"] = str(selected_id)
                    st.info("Open the Adventures tab to edit the selected entry.")
            st.caption(f"{len(map_data)} adventure(s) with coordinates. Click a pin to select an adventure.")
        else:
            st.info("No map coordinates saved yet. Add latitude and longitude to an adventure to show it here.")
            st.markdown("[Find coordinates with Google Maps](https://support.google.com/maps/answer/18539)")
    else:
        st.info("Your map will appear here once you add adventures with coordinates.")

with tab_add:
    st.markdown("<div class='dd-section'>✦ Pin a new adventure</div>", unsafe_allow_html=True)
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("Adventure name *", placeholder="e.g. Lynn Canyon Loop")
        category = st.selectbox("Adventure type", CATEGORIES)
        location = st.text_input("Location", placeholder="e.g. North Vancouver, BC")
        col1, col2 = st.columns(2)
        distance = col1.number_input("Distance in km (0 if not applicable)", min_value=0.0, value=0.0, step=0.5)
        elevation_gain = col2.number_input("Elevation gain in metres (0 if unknown)", min_value=0, value=0, step=25)
        difficulty = st.selectbox("Difficulty", DIFFICULTIES)
        status = st.selectbox("Status", STATUSES)
        notes = st.text_area("Notes", placeholder="Parking, best time to go, things to bring...")
        map_url = st.text_input("Website or map link", placeholder="https://...")
        photo_url = st.text_input("Photo URL (optional)", placeholder="Paste a direct image link")
        uploaded_photo = st.file_uploader(
            "Or upload a photo (optional)",
            type=["jpg", "jpeg", "png", "webp", "gif"],
            key="new_adventure_photo",
        )
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
                chosen_photo_url = photo_url.strip() or None
                if uploaded_photo is not None:
                    chosen_photo_url = upload_adventure_photo(uploaded_photo)
                save_adventure({
                    "name": name.strip(), "category": category, "location": location.strip(),
                    "distance_km": distance if distance > 0 else None, "elevation_gain_m": elevation_gain if elevation_gain > 0 else None, "difficulty": difficulty,
                    "status": status, "notes": notes.strip(), "map_url": map_url.strip(),
                    "latitude": latitude if latitude != 0 else None,
                    "longitude": longitude if longitude != 0 else None,
                    "photo_url": chosen_photo_url,
                })
                st.success(f"Added '{name.strip()}' to The Dilly Dally List!")
                st.rerun()
            except Exception as exc:
                st.error("Could not save this adventure. Check the database setup.")
                st.code(str(exc))

with tab_import:
    st.markdown("<div class='dd-section'>✿ Bring your old list along</div>", unsafe_allow_html=True)
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
                "elevation_gain_m": ["elevation_gain_m", "elevation gain", "elevation_gain", "elevation", "gain (m)", "elevation gain (m)", "ascent", "ascent (m)"],
                "difficulty": ["difficulty", "level"],
                "status": ["status", "progress"],
                "notes": ["notes", "description", "comments"],
                "map_url": ["map_url", "url", "website", "link"]
            }
            st.write("Match your spreadsheet columns:")
            for field, label in [
                ("name", "Adventure name *"), ("category", "Adventure type"), ("location", "Location"),
                ("distance_km", "Distance (km)"), ("elevation_gain_m", "Elevation gain (m)"), ("difficulty", "Difficulty"), ("status", "Status"),
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
                    elevation_val = None
                    if mappings["elevation_gain_m"] != "(skip this field)":
                        try:
                            elevation_val = float(str(rec.get(mappings["elevation_gain_m"], "")).replace(",", "."))
                            if elevation_val <= 0: elevation_val = None
                        except Exception:
                            elevation_val = None
                    values = {
                        "name": clean_text(rec.get(name_col, "")), "category": cat_val,
                        "location": clean_text(rec.get(mappings["location"], "")) if mappings["location"] != "(skip this field)" else "",
                        "distance_km": distance_val, "elevation_gain_m": elevation_val, "difficulty": diff_val, "status": status_val,
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
st.caption("Made for spontaneous plans and happy detours, it's always fun to get a little lost.")
