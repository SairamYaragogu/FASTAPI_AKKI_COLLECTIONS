import streamlit as pd_st
import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import io
from config import BACKEND_URL, ADMIN_USERNAME, ADMIN_PASSWORD, OPENAI_API_KEY, OPENAI_MODEL
from rag_service import get_rag_engine

# Set page configuration with Flipkart blue theme icon
st.set_page_config(
    page_title="AKKI LATEST COLLECTIONS | Flipkart Style Fashion",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session States
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"  # 'home', 'detail', 'admin', 'cart'
if "selected_product_id" not in st.session_state:
    st.session_state.selected_product_id = None
if "selected_category" not in st.session_state:
    st.session_state.selected_category = "All"
if "selected_subcategory" not in st.session_state:
    st.session_state.selected_subcategory = "All"
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "cart" not in st.session_state:
    st.session_state.cart = []
if "selected_image_index" not in st.session_state:
    st.session_state.selected_image_index = 0
if "admin_table_page" not in st.session_state:
    st.session_state.admin_table_page = 0
if "policy_chat_history" not in st.session_state:
    st.session_state.policy_chat_history = [
        {
            "role": "assistant",
            "content": "👋 **Welcome to the AKKI User Guide & Shopping Assistant!**\n\nI am your personal shopping guide for **AKKI LATEST COLLECTIONS**. You can ask me about:\n- 🥻 **Sarees Collection** (Banarasi, Soft Silk, Chanderi, Kanjivaram & more)\n- 👗 **Dress Materials & Suit Sets** (Chanderi, Bandhani, Jamdani)\n- ✨ **Ready-to-wear Dresses & Gowns**\n- 🚚 **Free Shipping, COD & 7-Day Replacement Policy**",
            "sources": []
        }
    ]
if "pending_policy_query" not in st.session_state:
    st.session_state.pending_policy_query = None

# Custom CSS for Authentic Flipkart Aesthetics
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        background-color: #f1f3f6 !important;
        color: #212121;
    }
    
    /* Top Header Bar */
    .fk-header {
        background-color: #2874f0;
        padding: 12px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        color: white;
        box-shadow: 0 1px 4px rgba(0,0,0,0.1);
        margin-bottom: 12px;
        border-radius: 8px;
    }
    .fk-logo {
        font-size: 22px;
        font-weight: 700;
        font-style: italic;
        letter-spacing: 0.5px;
        color: #ffffff;
        text-decoration: none;
    }
    .fk-sublogo {
        font-size: 11px;
        font-style: italic;
        color: #ffe500;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 3px;
    }
    .fk-badge-plus {
        color: #ffe500;
        font-weight: bold;
    }
    
    /* Flipkart Category Bar */
    .fk-cat-container {
        background: #ffffff;
        padding: 12px 18px;
        border-radius: 6px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.06);
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        justify-content: space-around;
        gap: 15px;
        overflow-x: auto;
    }
    
    /* Product Card Styling */
    .product-card {
        background: #ffffff;
        border-radius: 6px;
        padding: 12px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        border: 1px solid #f0f0f0;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
        margin-bottom: 15px;
    }
    .product-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        border-color: #e0e0e0;
    }
    .product-img-wrapper {
        width: 100%;
        height: 240px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        background: #fafafa;
        border-radius: 4px;
        margin-bottom: 10px;
        position: relative;
    }
    .product-img-wrapper img {
        max-width: 100%;
        max-height: 100%;
        object-fit: cover;
        transition: transform 0.3s ease;
    }
    .product-card:hover .product-img-wrapper img {
        transform: scale(1.04);
    }
    .product-title {
        font-size: 14px;
        font-weight: 500;
        color: #212121;
        line-height: 1.3;
        margin-bottom: 4px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        height: 36px;
    }
    .product-subcategory {
        font-size: 12px;
        color: #878787;
        margin-bottom: 6px;
    }
    .rating-badge {
        background-color: #388e3c;
        color: white;
        font-size: 12px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 3px;
        display: inline-flex;
        align-items: center;
        gap: 3px;
        width: fit-content;
    }
    .review-count {
        color: #878787;
        font-size: 12px;
        margin-left: 5px;
        font-weight: 400;
    }
    .price-row {
        display: flex;
        align-items: baseline;
        gap: 8px;
        margin-top: 6px;
    }
    .selling-price {
        font-size: 17px;
        font-weight: 700;
        color: #212121;
    }
    .mrp-price {
        font-size: 13px;
        color: #878787;
        text-decoration: line-through;
    }
    .discount-pct {
        font-size: 13px;
        color: #388e3c;
        font-weight: 700;
    }
    .fassured-badge {
        height: 18px;
        vertical-align: middle;
        margin-left: 4px;
    }
    .offer-tag {
        font-size: 12px;
        color: #26a541;
        font-weight: 500;
        margin-top: 4px;
    }

    /* Flipkart Buttons */
    .btn-cart {
        background-color: #ff9f00 !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
        border-radius: 4px !important;
        border: none !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.2) !important;
        cursor: pointer !important;
        width: 100%;
        text-align: center;
    }
    .btn-buy {
        background-color: #fb641b !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
        border-radius: 4px !important;
        border: none !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.2) !important;
        cursor: pointer !important;
        width: 100%;
        text-align: center;
    }

    /* Detail Page */
    .detail-container {
        background: #ffffff;
        border-radius: 8px;
        padding: 24px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        margin-top: 10px;
    }
    .detail-title {
        font-size: 20px;
        font-weight: 500;
        color: #212121;
        margin-bottom: 8px;
    }
    .offer-box {
        background-color: #f9fbf9;
        border-left: 4px solid #388e3c;
        padding: 10px 14px;
        border-radius: 0 4px 4px 0;
        margin: 12px 0;
        font-size: 13px;
    }
    .offer-item {
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .offer-tag-icon {
        color: #388e3c;
        font-weight: bold;
    }
    .thumbnail-img {
        border: 2px solid #e0e0e0;
        border-radius: 4px;
        cursor: pointer;
        padding: 2px;
        margin-bottom: 8px;
        transition: border-color 0.2s;
    }
    .thumbnail-img:hover, .thumbnail-img.active {
        border-color: #2874f0;
    }
    
    /* Admin Header Card */
    .admin-card {
        background: #ffffff;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.07);
        margin-bottom: 20px;
    }

    /* Cart Items & Container Elevation */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.04) !important;
        padding: 16px 20px !important;
        margin-bottom: 16px !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12), 0 2px 6px rgba(0, 0, 0, 0.06) !important;
        border-color: #cbd5e1 !important;
    }

    /* Fixed uniform image wrapper for cart items */
    .cart-img-wrapper {
        width: 100%;
        height: 140px;
        min-height: 140px;
        max-height: 140px;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #f8fafc;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #f1f5f9;
    }

    .cart-item-img {
        max-width: 100%;
        max-height: 140px;
        width: auto;
        height: auto;
        object-fit: contain;
        display: block;
        margin: auto;
        transition: transform 0.3s ease;
    }

    .cart-img-wrapper:hover .cart-item-img {
        transform: scale(1.05);
    }

    /* Fallback in case st.image is rendered in container */
    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stImage"] {
        height: 140px !important;
        max-height: 140px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background: #f8fafc !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        border: 1px solid #f1f5f9 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stImage"] img {
        max-height: 140px !important;
        max-width: 100% !important;
        width: auto !important;
        height: auto !important;
        object-fit: contain !important;
        margin: auto !important;
    }

    /* Cart Item Typography & Elements with Uniform Row Heights */
    .cart-item-title {
        font-size: 15px;
        font-weight: 600;
        color: #212121;
        margin-bottom: 4px;
        line-height: 1.35;
        height: 40px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    .cart-item-meta {
        font-size: 12px;
        color: #878787;
        margin-bottom: 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        height: 18px;
    }

    .cart-item-delivery {
        font-size: 12px;
        color: #26a541;
        font-weight: 500;
        margin-top: 6px;
        height: 18px;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    /* Price Details Card Styling */
    .price-details-title {
        font-size: 14px;
        font-weight: 700;
        color: #878787;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding-bottom: 8px;
        border-bottom: 1px solid #f0f0f0;
        margin-bottom: 12px;
    }

    .price-breakdown-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 14px;
        color: #212121;
        margin-bottom: 10px;
    }

    .price-total-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        font-size: 17px;
        font-weight: 700;
        color: #212121;
        padding-top: 10px;
        margin-top: 10px;
        border-top: 1px dashed #e0e0e0;
        margin-bottom: 12px;
    }

    .saving-badge {
        background: #e8f5e9;
        color: #2e7d32;
        font-size: 13px;
        font-weight: 600;
        padding: 8px 12px;
        border-radius: 6px;
        margin-bottom: 14px;
    }

    /* Remove button styling inside cart cards */
    div[data-testid="stVerticalBlockBorderWrapper"] button[data-testid="baseButton-secondary"],
    div[data-testid="stVerticalBlockBorderWrapper"] button[kind="secondary"] {
        border: 1px solid #e0e0e0 !important;
        color: #64748b !important;
        font-weight: 500 !important;
        border-radius: 4px !important;
        transition: all 0.2s ease !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] button[data-testid="baseButton-secondary"]:hover,
    div[data-testid="stVerticalBlockBorderWrapper"] button[kind="secondary"]:hover {
        border-color: #d32f2f !important;
        color: #d32f2f !important;
        background-color: #fff5f5 !important;
    }

    /* =========================================================================
       FLOATING RIGHT-BOTTOM COMPANY POLICY CHATBOT
       ========================================================================= */
    div[data-testid="stElementContainer"]:has(div[data-testid="stPopover"]),
    div[data-testid="element-container"]:has(div[data-testid="stPopover"]),
    div.element-container:has(.stPopover) {
        position: fixed !important;
        bottom: 24px !important;
        right: 24px !important;
        left: auto !important;
        top: auto !important;
        width: auto !important;
        min-width: 0 !important;
        max-width: fit-content !important;
        margin: 0 !important;
        padding: 0 !important;
        z-index: 999999 !important;
        display: flex !important;
        justify-content: flex-end !important;
    }

    div[data-testid="stPopover"],
    .stPopover {
        position: fixed !important;
        bottom: 24px !important;
        right: 24px !important;
        left: auto !important;
        top: auto !important;
        width: auto !important;
        min-width: 0 !important;
        max-width: fit-content !important;
        margin: 0 !important;
        padding: 0 !important;
        z-index: 999999 !important;
        display: flex !important;
        justify-content: flex-end !important;
        align-items: flex-end !important;
    }

    div[data-testid="stPopover"] > button,
    .stPopover > button,
    div[data-testid="stPopover"] button[data-testid="baseButton-secondary"],
    div[data-testid="stPopover"] button[kind="secondary"] {
        position: relative !important;
        background: linear-gradient(135deg, #2874f0 0%, #1251b5 100%) !important;
        color: #ffffff !important;
        font-family: 'Roboto', sans-serif !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        border-radius: 50px !important;
        border: 2px solid #ffffff !important;
        box-shadow: 0 6px 20px rgba(40, 116, 240, 0.45) !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 8px !important;
        cursor: pointer !important;
        margin: 0 !important;
        float: right !important;
        transition: all 0.25s ease-in-out !important;
    }

    div[data-testid="stPopover"] > button:hover,
    .stPopover > button:hover {
        transform: translateY(-2px) scale(1.03) !important;
        box-shadow: 0 10px 28px rgba(40, 116, 240, 0.65) !important;
        background: linear-gradient(135deg, #1b62d8 0%, #0d429a 100%) !important;
        color: #ffffff !important;
        border-color: #ffffff !important;
    }

    div[data-testid="stPopoverBody"] {
        width: 470px !important;
        min-width: 380px !important;
        max-width: 95vw !important;
        height: 660px !important;
        max-height: 86vh !important;
        border-radius: 14px !important;
        box-shadow: 0 20px 55px rgba(0, 0, 0, 0.28) !important;
        border: 1px solid #cbd5e1 !important;
        background: #ffffff !important;
        padding: 16px !important;
        overflow-y: auto !important;
        z-index: 9999999 !important;
        display: flex !important;
        flex-direction: column !important;
    }

    div[data-testid="stPopoverBody"] > div[data-testid="stVerticalBlock"],
    div[data-testid="stPopoverBody"] > div.stVerticalBlock,
    div[data-testid="stPopoverBody"] > div:first-child {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 1 auto !important;
        min-height: 100% !important;
        width: 100% !important;
    }

    /* Sticky top header inside chat window */
    .chat-sticky-header {
        position: sticky !important;
        top: -16px !important;
        background: #ffffff !important;
        z-index: 99 !important;
        padding: 2px 0 8px 0 !important;
        margin-bottom: 4px !important;
    }

    /* Top bar gradient matching bottom button */
    .chat-top-banner {
        background: linear-gradient(135deg, #2874f0 0%, #1251b5 100%) !important;
        color: #ffffff !important;
        padding: 13px 16px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 16px rgba(40, 116, 240, 0.35) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
    }

    .chat-online-badge {
        background: #10b981 !important;
        color: #ffffff !important;
        font-size: 10px !important;
        font-weight: 700 !important;
        padding: 3px 9px !important;
        border-radius: 20px !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 2px 6px rgba(16, 185, 129, 0.4) !important;
    }

    /* Flex spacer ensuring input box is always pushed to bottom */
    div[data-testid="stElementContainer"]:has(.chat-flex-spacer),
    .chat-flex-spacer {
        flex: 1 1 auto !important;
        min-height: 16px !important;
    }

    /* Fixed/Sticky bottom input text area pinned to the bottom */
    div[data-testid="stPopoverBody"] div[data-testid="stElementContainer"]:has(form[data-testid="stForm"]),
    div[data-testid="stPopoverBody"] div.element-container:has(form),
    div[data-testid="stPopoverBody"] div:has(> form[data-testid="stForm"]) {
        margin-top: auto !important;
        position: sticky !important;
        bottom: -16px !important;
        background: #ffffff !important;
        z-index: 99 !important;
        padding: 10px 0 2px 0 !important;
        border-top: 1px solid #e2e8f0 !important;
        width: 100% !important;
    }

    div[data-testid="stPopoverBody"] form[data-testid="stForm"] {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 6px 8px !important;
        margin: 0 !important;
    }

    /* =========================================================================
       UNIVERSAL THEME COMPATIBILITY (LIGHT & DARK MODE VISIBILITY FIX)
       Ensures all text, chat messages, FAQ buttons, avatars, and input boxes
       inside the popover are crisp, dark, and 100% visible in Dark Mode too.
       ========================================================================= */

    /* Ensure all text in chat messages is crisp dark slate (does not affect header banner) */
    div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] p,
    div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] li,
    div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] span,
    div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] strong,
    div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] b,
    div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] h1,
    div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] h2,
    div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] h3,
    div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] h4,
    div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] div,
    div[data-testid="stPopoverBody"] [data-testid="stChatMessageContent"] * {
        color: #1e293b !important;
    }

    /* Style Chat Message cards so they have high-contrast background & sharp text */
    div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        margin-bottom: 10px !important;
    }

    div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] * {
        color: #1e293b !important;
    }

    div[data-testid="stPopoverBody"] [data-testid="stChatMessage"] [data-testid="stChatMessageContent"] * {
        color: #1e293b !important;
    }

    /* Clean avatar styling (replaces dark square box with soft clean card) */
    div[data-testid="stPopoverBody"] [data-testid="stChatMessageAvatar"],
    div[data-testid="stPopoverBody"] .stChatMessageAvatar {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
    }

    /* FAQ Quick Question Buttons: Force readable light background & dark text in Dark Mode */
    div[data-testid="stPopoverBody"] button[kind="secondary"],
    div[data-testid="stPopoverBody"] button[data-testid="baseButton-secondary"],
    div[data-testid="stPopoverBody"] div[data-testid="stElementContainer"] > div > div > button {
        background-color: #f8fafc !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.2s ease !important;
    }

    div[data-testid="stPopoverBody"] button[kind="secondary"] p,
    div[data-testid="stPopoverBody"] button[data-testid="baseButton-secondary"] p,
    div[data-testid="stPopoverBody"] button[kind="secondary"] span,
    div[data-testid="stPopoverBody"] button[data-testid="baseButton-secondary"] span,
    div[data-testid="stPopoverBody"] div[data-testid="stElementContainer"] > div > div > button p,
    div[data-testid="stPopoverBody"] div[data-testid="stElementContainer"] > div > div > button span {
        color: #1e293b !important;
        font-weight: 500 !important;
    }

    div[data-testid="stPopoverBody"] button[kind="secondary"]:hover,
    div[data-testid="stPopoverBody"] button[data-testid="baseButton-secondary"]:hover {
        background-color: #eff6ff !important;
        border-color: #2874f0 !important;
        box-shadow: 0 2px 8px rgba(40, 116, 240, 0.2) !important;
        transform: translateY(-1px) !important;
    }

    div[data-testid="stPopoverBody"] button[kind="secondary"]:hover p,
    div[data-testid="stPopoverBody"] button[data-testid="baseButton-secondary"]:hover p,
    div[data-testid="stPopoverBody"] button[kind="secondary"]:hover span,
    div[data-testid="stPopoverBody"] button[data-testid="baseButton-secondary"]:hover span {
        color: #1e40af !important;
    }

    /* Fixed/Sticky bottom input box and text field in Dark Mode */
    div[data-testid="stPopoverBody"] div[data-testid="stTextInputRootElement"],
    div[data-testid="stPopoverBody"] div[data-testid="stTextInputRootElement"] > div,
    div[data-testid="stPopoverBody"] div[data-testid="stTextInput"] > div > div {
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }

    div[data-testid="stPopoverBody"] input[data-testid="stTextInputRootElement"],
    div[data-testid="stPopoverBody"] input[type="text"],
    div[data-testid="stPopoverBody"] input {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        font-size: 14px !important;
        -webkit-text-fill-color: #0f172a !important;
    }

    div[data-testid="stPopoverBody"] input::placeholder {
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
        opacity: 1 !important;
    }

    /* Completely hide 'Press Enter to submit form' helper tag */
    div[data-testid="stPopoverBody"] [data-testid="InputInstructions"],
    div[data-testid="stPopoverBody"] div[data-testid="InputInstructions"],
    div[data-testid="stPopoverBody"] span[data-testid="InputInstructions"],
    div[data-testid="InputInstructions"],
    [data-testid="InputInstructions"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0 !important;
        width: 0 !important;
        pointer-events: none !important;
    }

    /* Send button inside form */
    div[data-testid="stPopoverBody"] form[data-testid="stForm"] button[kind="primary"],
    div[data-testid="stPopoverBody"] form[data-testid="stForm"] button[kind="secondary"],
    div[data-testid="stPopoverBody"] form[data-testid="stForm"] button {
        background: linear-gradient(135deg, #2874f0 0%, #1251b5 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    div[data-testid="stPopoverBody"] form[data-testid="stForm"] button p,
    div[data-testid="stPopoverBody"] form[data-testid="stForm"] button span {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* Top banner white text guarantee (Title & Subtitle 100% white) */
    div[data-testid="stPopoverBody"] .chat-top-banner,
    div[data-testid="stPopoverBody"] .chat-top-banner *,
    div[data-testid="stPopoverBody"] [data-testid="stMarkdownContainer"] .chat-top-banner,
    div[data-testid="stPopoverBody"] [data-testid="stMarkdownContainer"] .chat-top-banner *,
    div[data-testid="stPopoverBody"] [data-testid="stMarkdownContainer"] .chat-top-banner div,
    div[data-testid="stPopoverBody"] [data-testid="stMarkdownContainer"] .chat-top-banner span,
    div[data-testid="stPopoverBody"] [data-testid="stMarkdownContainer"] .chat-top-banner b,
    .chat-top-banner,
    .chat-top-banner *,
    .chat-top-title,
    .chat-top-subtitle {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    .chat-top-title,
    div[data-testid="stPopoverBody"] .chat-top-title,
    div[data-testid="stPopoverBody"] [data-testid="stMarkdownContainer"] .chat-top-title {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        letter-spacing: 0.3px !important;
    }

    .chat-top-subtitle,
    div[data-testid="stPopoverBody"] .chat-top-subtitle,
    div[data-testid="stPopoverBody"] [data-testid="stMarkdownContainer"] .chat-top-subtitle {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 11px !important;
        font-weight: 400 !important;
        letter-spacing: 0.2px !important;
        margin-top: 4px !important;
    }

    .policy-source-chip {
        display: inline-block;
        background: #f1f5f9;
        color: #334155;
        font-size: 11px;
        font-weight: 500;
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid #cbd5e1;
        margin-right: 5px;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Helper API functions
def fetch_api(endpoint: str, method="GET", data=None, files=None):
    url = f"{BACKEND_URL}{endpoint}"
    try:
        if method == "GET":
            res = requests.get(url, params=data, timeout=10)
        elif method == "POST":
            if files:
                res = requests.post(url, files=files, timeout=60)
            else:
                res = requests.post(url, json=data, timeout=15)
        elif method == "DELETE":
            res = requests.delete(url, timeout=10)
        return res
    except Exception as e:
        st.error(f"⚠️ Cannot connect to Backend API at {url}. Error: {e}")
        return None

def navigate_to(page: str, product_id=None):
    st.session_state.current_page = page
    if product_id is not None:
        st.session_state.selected_product_id = product_id
        st.session_state.selected_image_index = 0
    st.rerun()

def render_flipkart_gallery(images: list, title: str = "") -> str:
    """Generates Flipkart-style image viewer with pinch/hover zoom and real thumbnails."""
    if not images:
        images = ["https://res.cloudinary.com/dh96id3hk/image/upload/v1757262322/146691a5-d2a3-4bf8-9835-afa771aa532f_vcxodf.jpg"]

    images_json = json.dumps(images)
    escaped_title = title.replace('"', '&quot;')

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            user-select: none;
        }}
        body {{
            background: transparent;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            overflow: hidden;
            display: flex;
            justify-content: center;
        }}
        .gallery-wrap {{
            width: 100%;
            max-width: 500px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        .main-box {{
            position: relative;
            width: 100%;
            height: 420px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            cursor: crosshair;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        .main-img {{
            max-width: 92%;
            max-height: 92%;
            object-fit: contain;
            transition: transform 0.12s ease-out;
            transform-origin: center center;
            will-change: transform;
        }}
        .zoom-badge {{
            position: absolute;
            bottom: 10px;
            right: 10px;
            background: rgba(15, 23, 42, 0.75);
            color: #ffffff;
            font-size: 11px;
            font-weight: 500;
            padding: 4px 10px;
            border-radius: 20px;
            pointer-events: none;
            backdrop-filter: blur(4px);
        }}
        .thumbs-container {{
            display: flex;
            gap: 10px;
            overflow-x: auto;
            padding: 4px 2px;
            scrollbar-width: thin;
        }}
        .thumbs-container::-webkit-scrollbar {{
            height: 4px;
        }}
        .thumbs-container::-webkit-scrollbar-thumb {{
            background: #cbd5e1;
            border-radius: 4px;
        }}
        .thumb-box {{
            width: 60px;
            height: 60px;
            flex-shrink: 0;
            border-radius: 6px;
            border: 2px solid #e2e8f0;
            background: #ffffff;
            overflow: hidden;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0.75;
        }}
        .thumb-box:hover {{
            opacity: 1;
            border-color: #93c5fd;
        }}
        .thumb-box.active {{
            opacity: 1;
            border-color: #2874f0;
            box-shadow: 0 0 0 2px rgba(40, 116, 240, 0.35);
        }}
        .thumb-box img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
    </style>
    </head>
    <body>
        <div class="gallery-wrap">
            <div class="main-box" id="zoomBox">
                <img src="{images[0]}" alt="{escaped_title}" class="main-img" id="mainImg">
                <div class="zoom-badge">🔍 Hover cursor / Pinch to zoom</div>
            </div>
            <div class="thumbs-container" id="thumbsRow"></div>
        </div>

        <script>
            const images = {images_json};
            let currentIndex = 0;
            let currentScale = 1;
            const zoomBox = document.getElementById('zoomBox');
            const mainImg = document.getElementById('mainImg');
            const thumbsRow = document.getElementById('thumbsRow');

            function renderThumbs() {{
                if (images.length <= 1) {{
                    thumbsRow.style.display = 'none';
                    return;
                }}
                thumbsRow.innerHTML = '';
                images.forEach((url, idx) => {{
                    const card = document.createElement('div');
                    card.className = 'thumb-box' + (idx === currentIndex ? ' active' : '');
                    card.onclick = () => selectImage(idx);
                    
                    const img = document.createElement('img');
                    img.src = url;
                    card.appendChild(img);
                    thumbsRow.appendChild(card);
                }});
            }}

            function selectImage(idx) {{
                currentIndex = idx;
                mainImg.src = images[idx];
                mainImg.style.transform = 'scale(1)';
                mainImg.style.transformOrigin = 'center center';
                currentScale = 1;
                
                const cards = thumbsRow.getElementsByClassName('thumb-box');
                for (let i = 0; i < cards.length; i++) {{
                    cards[i].classList.toggle('active', i === idx);
                }}
            }}

            // Mouse hover tracking for smooth Flipkart lens zoom
            zoomBox.addEventListener('mousemove', (e) => {{
                const rect = zoomBox.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / rect.width) * 100;
                const y = ((e.clientY - rect.top) / rect.height) * 100;
                mainImg.style.transformOrigin = `${{x}}% ${{y}}%`;
                const scale = Math.max(currentScale, 2.2);
                mainImg.style.transform = `scale(${{scale}})`;
            }});

            zoomBox.addEventListener('mouseleave', () => {{
                mainImg.style.transform = 'scale(1)';
                mainImg.style.transformOrigin = 'center center';
                currentScale = 1;
            }});

            // Scroll wheel zoom
            zoomBox.addEventListener('wheel', (e) => {{
                e.preventDefault();
                const rect = zoomBox.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / rect.width) * 100;
                const y = ((e.clientY - rect.top) / rect.height) * 100;
                mainImg.style.transformOrigin = `${{x}}% ${{y}}%`;
                
                if (e.deltaY < 0) {{
                    currentScale = Math.min(3.5, currentScale + 0.3);
                }} else {{
                    currentScale = Math.max(1, currentScale - 0.3);
                }}
                mainImg.style.transform = `scale(${{currentScale}})`;
            }}, {{ passive: false }});

            // Touch Pinch zoom support
            let initialDistance = 0;
            zoomBox.addEventListener('touchstart', (e) => {{
                if (e.touches.length === 2) {{
                    initialDistance = Math.hypot(
                        e.touches[0].clientX - e.touches[1].clientX,
                        e.touches[0].clientY - e.touches[1].clientY
                    );
                }}
            }});

            zoomBox.addEventListener('touchmove', (e) => {{
                if (e.touches.length === 2) {{
                    const currentDistance = Math.hypot(
                        e.touches[0].clientX - e.touches[1].clientX,
                        e.touches[0].clientY - e.touches[1].clientY
                    );
                    const diff = currentDistance - initialDistance;
                    if (diff > 0) {{
                        currentScale = Math.min(3.5, currentScale + 0.05);
                    }} else {{
                        currentScale = Math.max(1, currentScale - 0.05);
                    }}
                    mainImg.style.transform = `scale(${{currentScale}})`;
                }}
            }});

            renderThumbs();
        </script>
    </body>
    </html>
    """

# --- TOP FLIPKART NAVIGATION HEADER ---
col_logo, col_search, col_actions = st.columns([2.5, 4.5, 3])

with col_logo:
    st.markdown("""
    <div style="cursor: pointer; padding-top: 4px;" onclick="window.location.reload();">
        <span style="font-size: 24px; font-weight: 800; color: #2874f0; letter-spacing: 0.5px;">AKKI LATEST COLLECTIONS</span><br>
        <span style="font-size: 12px; color: #878787; font-weight: 500;">
            Explore <span style="color: #ff9f00; font-weight: bold;">Plus ✦</span>
        </span>
    </div>
    """, unsafe_allow_html=True)

with col_search:
    search_val = st.text_input(
        "Search",
        value=st.session_state.search_query,
        placeholder="🔍 Search for Sarees, Dress Materials, Cotton and more...",
        label_visibility="collapsed",
        key="search_input"
    )
    if search_val != st.session_state.search_query:
        st.session_state.search_query = search_val
        st.session_state.current_page = "home"
        st.rerun()

with col_actions:
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
    with btn_col1:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.selected_category = "All"
            st.session_state.selected_subcategory = "All"
            st.session_state.search_query = ""
            navigate_to("home")
    with btn_col2:
        cart_count = len(st.session_state.cart)
        cart_label = f"🛒 Cart ({cart_count})" if cart_count > 0 else "🛒 Cart"
        if st.button(cart_label, use_container_width=True):
            navigate_to("cart")
    with btn_col3:
        admin_label = "⚙️ Admin" if not st.session_state.admin_logged_in else "👑 Admin ✔"
        if st.button(admin_label, use_container_width=True):
            navigate_to("admin")

st.markdown("<hr style='margin: 8px 0 16px 0; border: 0.5px solid #e0e0e0;'>", unsafe_allow_html=True)

# ==============================================================================
# PAGE 1: ADMIN DASHBOARD
# ==============================================================================
if st.session_state.current_page == "admin":
    st.markdown("### 🔒 Akki Admin Panel & Stock Inventory Manager")
    
    if not st.session_state.admin_logged_in:
        # Admin Login Screen
        st.info("Please sign in with Admin credentials to upload stock data and manage inventory.")
        login_col1, login_col2, login_col3 = st.columns([1, 1.5, 1])
        with login_col2:
            st.subheader("Admin Login")
            u_name = st.text_input("Username", value="admin")
            u_pwd = st.text_input("Password", type="password", value="admin123")
            if st.button("🔐 Login as Admin", type="primary", use_container_width=True):
                login_res = fetch_api("/api/admin/login", method="POST", data={"username": u_name, "password": u_pwd})
                if login_res and login_res.status_code == 200:
                    data = login_res.json()
                    if data.get("authenticated"):
                        st.session_state.admin_logged_in = True
                        st.success("Authentication successful! Welcome, Admin.")
                        st.rerun()
                    else:
                        st.error(data.get("message", "Invalid credentials."))
                else:
                    st.error("Authentication failed. Please verify FastAPI backend.")
    else:
        # Authenticated Admin Dashboard
        admin_top_col1, admin_top_col2 = st.columns([3, 1])
        with admin_top_col1:
            st.write(f"Logged in as **{ADMIN_USERNAME}** | Secure Session Active")
        with admin_top_col2:
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.admin_logged_in = False
                navigate_to("home")

        # Stats Cards
        stats_res = fetch_api("/api/stats")
        if stats_res and stats_res.status_code == 200:
            stats = stats_res.json()
            s_col1, s_col2, s_col3 = st.columns(3)
            s_col1.metric("📦 Total Products", stats.get("total_products", 0))
            s_col2.metric("🏷️ Categories", stats.get("total_categories", 0))
            s_col3.metric("📑 Subcategories", stats.get("total_subcategories", 0))

        # Excel Upload Section
        st.subheader("📤 Upload Stock Entry Excel File (`stock_entry.xlsx`)")
        st.write("Upload your product catalog spreadsheet. The system will automatically read and update MySQL database inventory in real-time.")
        
        uploaded_file = st.file_uploader("Choose stock_entry.xlsx file", type=["xlsx", "xls"])
        if uploaded_file is not None:
            st.write(f"Selected file: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
            if st.button("🚀 Upload & Sync Inventory Now", type="primary"):
                with st.spinner("Processing Excel and updating MySQL database..."):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                    upload_res = fetch_api("/api/admin/upload-excel", method="POST", files=files)
                    if upload_res and upload_res.status_code == 200:
                        res_data = upload_res.json()
                        st.session_state.admin_table_page = 0
                        st.success(f"✅ {res_data.get('message')}")
                    else:
                        detail = upload_res.json().get("detail") if upload_res else "Unknown error"
                        st.error(f"❌ Upload failed: {detail}")

        # Current Database Inventory Table / Graphical View
        head_col1, head_col2 = st.columns([3, 1.2], vertical_alignment="center")
        with head_col1:
            st.subheader("📋 Current MySQL Product Inventory")
        with head_col2:
            show_graphical = st.toggle("📊 Graphical View", value=False, key="toggle_admin_graphical_view")

        all_prods_res = fetch_api("/api/products", data={"limit": 500})
        if all_prods_res and all_prods_res.status_code == 200:
            prods = all_prods_res.json()
            if prods:
                import pandas as pd
                cols = ["sno", "category", "subcategory", "title", "price", "mrp", "discount_pct", "rating", "stock_status"]
                df_all = pd.DataFrame(prods)
                display_cols = [c for c in cols if c in df_all.columns]
                df_view = df_all[display_cols]

                if not show_graphical:
                    # TABULAR VIEW (Existing functionality preserved)
                    # Pagination: 10 records per page
                    PAGE_SIZE = 10
                    total_records = len(df_view)
                    total_pages = max(1, (total_records + PAGE_SIZE - 1) // PAGE_SIZE)

                    # Ensure current page is within valid bounds
                    if st.session_state.admin_table_page >= total_pages:
                        st.session_state.admin_table_page = total_pages - 1
                    if st.session_state.admin_table_page < 0:
                        st.session_state.admin_table_page = 0

                    curr_page = st.session_state.admin_table_page
                    start_idx = curr_page * PAGE_SIZE
                    end_idx = min(start_idx + PAGE_SIZE, total_records)

                    df_page = df_view.iloc[start_idx:end_idx]
                    st.dataframe(df_page, hide_index=True, use_container_width=True)

                    # Pagination Controls: Prev & Next buttons at the bottom of the table
                    c_prev, c_info, c_next = st.columns([1, 2, 1])
                    with c_prev:
                        if st.button("⬅️ Previous", disabled=(curr_page == 0), key="btn_admin_prev", use_container_width=True):
                            st.session_state.admin_table_page = max(0, curr_page - 1)
                            st.rerun()
                    with c_info:
                        st.markdown(
                            f"<div style='text-align: center; padding-top: 6px; font-weight: 500; font-size: 14px;'>"
                            f"Page {curr_page + 1} of {total_pages} &nbsp;|&nbsp; Showing {start_idx + 1}–{end_idx} of {total_records} records"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    with c_next:
                        if st.button("Next ➡️", disabled=(curr_page >= total_pages - 1), key="btn_admin_next", use_container_width=True):
                            st.session_state.admin_table_page = min(total_pages - 1, curr_page + 1)
                            st.rerun()
                else:
                    # GRAPHICAL VIEW (Matplotlib Charts)
                    import matplotlib.pyplot as plt
                    import numpy as np

                    # Convert numerical columns safely
                    df_chart = df_all.copy()
                    df_chart['price'] = pd.to_numeric(df_chart['price'], errors='coerce').fillna(0)
                    df_chart['mrp'] = pd.to_numeric(df_chart['mrp'], errors='coerce').fillna(0)
                    df_chart['rating'] = pd.to_numeric(df_chart['rating'], errors='coerce').fillna(0)
                    df_chart['discount_pct'] = pd.to_numeric(df_chart['discount_pct'], errors='coerce').fillna(0)

                    # Chart Palette
                    primary_color = "#2874f0"
                    secondary_color = "#ff9f00"
                    success_color = "#388e3c"
                    palette = ["#2874f0", "#ff9f00", "#388e3c", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899"]

                    g_col1, g_col2 = st.columns(2)

                    # Chart 1: Product Count by Category
                    with g_col1:
                        fig1, ax1 = plt.subplots(figsize=(6, 4))
                        cat_counts = df_chart['category'].value_counts()
                        bars1 = ax1.bar(cat_counts.index, cat_counts.values, color=palette[:len(cat_counts)], edgecolor='none', width=0.55)
                        ax1.set_title("📦 Product Count by Category", fontsize=13, fontweight='bold', pad=12)
                        ax1.set_ylabel("Number of Products", fontsize=11)
                        ax1.grid(axis='y', linestyle='--', alpha=0.3)
                        ax1.spines['top'].set_visible(False)
                        ax1.spines['right'].set_visible(False)
                        ax1.tick_params(axis='x', rotation=15)
                        for bar in bars1:
                            yval = bar.get_height()
                            ax1.text(bar.get_x() + bar.get_width() / 2, yval + 0.3, int(yval), ha='center', va='bottom', fontsize=10, fontweight='bold')
                        plt.tight_layout()
                        st.pyplot(fig1, use_container_width=True)
                        plt.close(fig1)

                    # Chart 2: Average Selling Price vs MRP by Category
                    with g_col2:
                        fig2, ax2 = plt.subplots(figsize=(6, 4))
                        price_grp = df_chart.groupby('category')[['price', 'mrp']].mean().reset_index()
                        x = np.arange(len(price_grp))
                        width = 0.35
                        rects1 = ax2.bar(x - width/2, price_grp['price'], width, label='Selling Price', color=primary_color)
                        rects2 = ax2.bar(x + width/2, price_grp['mrp'], width, label='MRP', color=secondary_color)
                        ax2.set_title("💰 Avg Price vs MRP by Category (₹)", fontsize=13, fontweight='bold', pad=12)
                        ax2.set_xticks(x)
                        ax2.set_xticklabels(price_grp['category'], rotation=15)
                        ax2.set_ylabel("Price (₹)", fontsize=11)
                        ax2.grid(axis='y', linestyle='--', alpha=0.3)
                        ax2.spines['top'].set_visible(False)
                        ax2.spines['right'].set_visible(False)
                        ax2.legend(frameon=False)
                        for rect in rects1:
                            h = rect.get_height()
                            ax2.text(rect.get_x() + rect.get_width() / 2, h + 50, f"₹{h:,.0f}", ha='center', va='bottom', fontsize=8, rotation=0)
                        plt.tight_layout()
                        st.pyplot(fig2, use_container_width=True)
                        plt.close(fig2)

                    g_col3, g_col4 = st.columns(2)

                    # Chart 3: Category Inventory Share (Donut Chart)
                    with g_col3:
                        fig3, ax3 = plt.subplots(figsize=(6, 4))
                        cat_counts = df_chart['category'].value_counts()
                        wedges, texts, autotexts = ax3.pie(
                            cat_counts.values,
                            labels=cat_counts.index,
                            autopct='%1.1f%%',
                            startangle=140,
                            colors=palette[:len(cat_counts)],
                            wedgeprops=dict(width=0.45, edgecolor='white', linewidth=2)
                        )
                        for at in autotexts:
                            at.set_fontsize(9)
                            at.set_fontweight('bold')
                        ax3.set_title("🥧 Inventory Share by Category", fontsize=13, fontweight='bold', pad=12)
                        plt.tight_layout()
                        st.pyplot(fig3, use_container_width=True)
                        plt.close(fig3)

                    # Chart 4: Average Customer Rating by Category
                    with g_col4:
                        fig4, ax4 = plt.subplots(figsize=(6, 4))
                        rating_grp = df_chart.groupby('category')['rating'].mean().reset_index()
                        bars4 = ax4.bar(rating_grp['category'], rating_grp['rating'], color=success_color, width=0.55)
                        ax4.set_title("⭐ Customer Rating by Category", fontsize=13, fontweight='bold', pad=12)
                        ax4.set_ylabel("Average Rating (Out of 5)", fontsize=11)
                        ax4.set_ylim(0, 5.5)
                        ax4.axhline(y=4.0, color='gray', linestyle=':', alpha=0.6, label='4.0 Baseline')
                        ax4.grid(axis='y', linestyle='--', alpha=0.3)
                        ax4.spines['top'].set_visible(False)
                        ax4.spines['right'].set_visible(False)
                        ax4.tick_params(axis='x', rotation=15)
                        for bar in bars4:
                            yval = bar.get_height()
                            ax4.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, f"{yval:.2f} ★", ha='center', va='bottom', fontsize=9, fontweight='bold')
                        plt.tight_layout()
                        st.pyplot(fig4, use_container_width=True)
                        plt.close(fig4)
            else:
                st.warning("No products found in database. Upload stock_entry.xlsx above to populate.")

        if st.button("👀 Return to AKKI Store Front", type="secondary"):
            navigate_to("home")

# ==============================================================================
# PAGE 2: CART VIEW
# ==============================================================================
elif st.session_state.current_page == "cart":
    st.markdown("### 🛒 Shopping Cart")
    if not st.session_state.cart:
        with st.container(border=True):
            st.info("Your shopping cart is empty! Browse our saree and dress collections to add items.")
            if st.button("🛍️ Shop Now", type="primary"):
                navigate_to("home")
    else:
        cart_left, cart_right = st.columns([2.2, 1])
        total_mrp = 0
        total_selling = 0
        
        with cart_left:
            for idx, item in enumerate(st.session_state.cart):
                with st.container(border=True):
                    c1, c2, c3 = st.columns([1, 2.5, 0.9], vertical_alignment="center")
                    with c1:
                        img_url = item.get("primary_image")
                        if not img_url and item.get("image_urls"):
                            img_url = item["image_urls"][0]
                        if not img_url:
                            img_url = "https://res.cloudinary.com/dh96id3hk/image/upload/v1757262322/146691a5-d2a3-4bf8-9835-afa771aa532f_vcxodf.jpg"
                        st.markdown(
                            f"""
                            <div class="cart-img-wrapper">
                                <img src="{img_url}" alt="{item.get('title', 'Product')}" class="cart-item-img" onerror="this.onerror=null;this.src='https://res.cloudinary.com/dh96id3hk/image/upload/v1757262322/146691a5-d2a3-4bf8-9835-afa771aa532f_vcxodf.jpg';">
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    with c2:
                        st.markdown(f"<div class='cart-item-title' title='{item.get('title', '')}'>{item.get('title', '')}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='cart-item-meta'>Category: {item.get('category', 'Fashion')} | Fabric: {item.get('subcategory', 'General')}</div>", unsafe_allow_html=True)
                        price = item.get('price', 0)
                        mrp = item.get('mrp', price * 1.5)
                        st.markdown(f"<div class='price-row'><span class='selling-price'>₹{price:,.0f}</span> <span class='mrp-price'>₹{mrp:,.0f}</span> <span class='discount-pct'>{item.get('discount_pct', 35)}% off</span></div>", unsafe_allow_html=True)
                        st.markdown("<div class='cart-item-delivery'>Delivery by Tomorrow | <span style='color: #388e3c; font-weight: 600;'>Free ₹40</span></div>", unsafe_allow_html=True)
                    with c3:
                        if st.button("Remove", key=f"del_cart_{idx}", use_container_width=True):
                            st.session_state.cart.pop(idx)
                            st.rerun()
                total_selling += item.get("price", 0)
                total_mrp += item.get("mrp", item.get("price", 0) * 1.5)

        with cart_right:
            with st.container(border=True):
                st.markdown("<div class='price-details-title'>PRICE DETAILS</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='price-breakdown-row'>"
                    f"<span>Price ({len(st.session_state.cart)} items)</span>"
                    f"<span><b>₹{total_mrp:,.0f}</b></span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                total_discount = total_mrp - total_selling
                st.markdown(
                    f"<div class='price-breakdown-row'>"
                    f"<span>Discount</span>"
                    f"<span style='color: #388e3c;'><b>- ₹{total_discount:,.0f}</b></span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<div class='price-breakdown-row'>"
                    f"<span>Delivery Charges</span>"
                    f"<span style='color: #388e3c;'><b>FREE</b></span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<div class='price-total-row'>"
                    f"<span>Total Amount</span>"
                    f"<span>₹{total_selling:,.0f}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<div class='saving-badge'>🌟 You will save ₹{total_discount:,.0f} on this order</div>",
                    unsafe_allow_html=True
                )
                if st.button("⚡ PLACE ORDER", type="primary", use_container_width=True):
                    st.success("🎉 Order Placed Successfully! Thank you for shopping with AKKI LATEST COLLECTIONS.")
                    st.session_state.cart = []
                if st.button("← Continue Shopping", use_container_width=True):
                    navigate_to("home")

# ==============================================================================
# PAGE 3: FLIPKART STYLE PRODUCT DETAILS PAGE
# ==============================================================================
elif st.session_state.current_page == "detail":
    prod_id = st.session_state.selected_product_id
    detail_res = fetch_api(f"/api/products/{prod_id}")
    
    if not detail_res or detail_res.status_code != 200:
        st.error("Product details could not be retrieved.")
        if st.button("← Back to Products"):
            navigate_to("home")
    else:
        product = detail_res.json()
        
        # Breadcrumbs
        st.markdown(f"""
        <div style="font-size: 13px; color: #94a3b8; margin-bottom: 14px;">
            <span style="color: #60a5fa; cursor: pointer;">Home</span> &gt; 
            <span style="color: #60a5fa;">{product.get('category')}</span> &gt; 
            <span style="color: #94a3b8;">{product.get('subcategory')}</span> &gt; 
            <span style="color: #f1f5f9; font-weight: 600;">{product.get('title')}</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("← Back to Products Listing"):
            navigate_to("home")

        img_col, details_col = st.columns([1.8, 2.2], gap="large")
        
        images = product.get("image_urls") or []
        if not images and product.get("primary_image"):
            images = [product.get("primary_image")]

        # Left Column: Image Gallery with Flipkart Hover/Pinch Zoom & Thumbnails
        with img_col:
            # Interactive Flipkart Zoom and Thumbnail Component
            gallery_html = render_flipkart_gallery(images, product.get('title', ''))
            gallery_height = 510 if len(images) > 1 else 440
            components.html(gallery_html, height=gallery_height)

            # Flipkart Action Buttons
            btn_add_col, btn_buy_col = st.columns(2)
            with btn_add_col:
                if st.button("🛒 ADD TO CART", type="secondary", use_container_width=True):
                    st.session_state.cart.append(product)
                    st.toast(f"Added {product.get('title')} to cart!", icon="🛒")
                    st.rerun()
            with btn_buy_col:
                if st.button("⚡ BUY NOW", type="primary", use_container_width=True):
                    st.session_state.cart.append(product)
                    navigate_to("cart")

        # Right Column: Flipkart Product Details & High-Contrast Pricing
        with details_col:
            # Product Title
            st.markdown(f"""
            <div style="font-size: 24px; font-weight: 700; color: #111827; line-height: 1.35; margin-bottom: 6px;">
                {product.get('title')}
            </div>
            """, unsafe_allow_html=True)
            
            # Subcategory & Fabric
            st.markdown(f"""
            <div style="font-size: 13.5px; color: #6b7280; margin-bottom: 10px;">
                Category: <b style="color: #111827;">{product.get('category')}</b> | 
                Fabric/Type: <b style="color: #111827;">{product.get('subcategory')}</b>
            </div>
            """, unsafe_allow_html=True)
            
            # Rating & Assured Badge
            rating = product.get("rating", 4.3)
            reviews = product.get("reviews_count", 120)
            st.markdown(f"""
            <div style="margin: 10px 0; display: flex; align-items: center; gap: 12px;">
                <span style="background-color: #16a34a; color: #ffffff; font-size: 13px; font-weight: 700; padding: 3px 8px; border-radius: 4px; display: inline-flex; align-items: center; gap: 3px;">
                    {rating} ★
                </span>
                <span style="color: #6b7280; font-size: 13px;">
                    <b style="color: #374151;">{reviews} Ratings</b> &amp; 42 Reviews
                </span>
                <span style="color: #2874f0; font-weight: 800; font-style: italic; font-size: 13px; background: #e8f0fe; padding: 3px 10px; border-radius: 4px;">
                    ✔ f-Assured
                </span>
            </div>
            """, unsafe_allow_html=True)

            # Price Section
            price = product.get("price", 0)
            mrp = product.get("mrp", price * 1.5)
            discount = product.get("discount_pct", 35)

            st.markdown(f"""
            <div style="margin: 16px 0;">
                <span style="color: #16a34a; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Special price</span><br>
                <span style="font-size: 32px; font-weight: 800; color: #111827;">₹{price:,.0f}</span>
                <span style="font-size: 16px; color: #6b7280; text-decoration: line-through; margin: 0 10px;">₹{mrp:,.0f}</span>
                <span style="font-size: 16px; color: #16a34a; font-weight: 700;">{discount}% off</span>
            </div>
            """, unsafe_allow_html=True)

            # Available Offers (Clear & High Contrast)
            st.markdown("""
            <div style="background-color: #0b2e1b; border: 1px solid #10b981; border-left: 5px solid #10b981; padding: 14px 18px; border-radius: 6px; margin: 16px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.06);">
                <div style="font-weight: 700; font-size: 15px; margin-bottom: 8px; color: #34d399;">🏷️ Available Offers</div>
                <div style="margin-bottom: 6px; color: #ecfdf5; font-size: 13.5px; line-height: 1.5;">🏷️ <b style="color: #a7f3d0;">Bank Offer:</b> 10% instant discount on ICICI &amp; HDFC Bank Cards up to ₹1,500</div>
                <div style="margin-bottom: 6px; color: #ecfdf5; font-size: 13.5px; line-height: 1.5;">🏷️ <b style="color: #a7f3d0;">Special Price:</b> Extra 15% off applied at checkout</div>
                <div style="margin-bottom: 6px; color: #ecfdf5; font-size: 13.5px; line-height: 1.5;">🏷️ <b style="color: #a7f3d0;">Partner Offer:</b> Buy this item &amp; get ₹500 off on next purchase</div>
                <div style="color: #ecfdf5; font-size: 13.5px; line-height: 1.5;">🏷️ <b style="color: #a7f3d0;">No Cost EMI:</b> Avail No Cost EMI on select cards from ₹299/month</div>
            </div>
            """, unsafe_allow_html=True)

            # Delivery & Assurances
            st.markdown("""
            <div style="margin: 16px 0; font-size: 13.5px; line-height: 1.9; color: #374151;">
                <div>🚚 <b style="color: #111827;">Delivery:</b> Free Delivery in 2-3 business days</div>
                <div>🔄 <b style="color: #111827;">Replacement:</b> 7 Days Replacement Policy</div>
                <div>💵 <b style="color: #111827;">Payment:</b> Cash on Delivery available</div>
                <div>🛡️ <b style="color: #111827;">Warranty:</b> 100% Authentic Quality Assured by Akki Collections</div>
            </div>
            """, unsafe_allow_html=True)

            # Description
            st.markdown("<div style='font-size: 16px; font-weight: 700; color: #111827; margin-top: 18px; margin-bottom: 6px;'>Product Description</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='color: #4b5563; font-size: 14px; line-height: 1.6;'>{product.get('description') or 'Premium quality ethnic wear curated with elegance for festivals, parties, and daily graceful attire.'}</div>", unsafe_allow_html=True)

            # Specifications Table
            st.markdown("<div style='font-size: 16px; font-weight: 700; color: #111827; margin-top: 20px; margin-bottom: 8px;'>Specifications</div>", unsafe_allow_html=True)
            spec_data = {
                "Catalog S.No": product.get("sno"),
                "Collection Name": product.get("title"),
                "Category": product.get("category"),
                "Fabric / Subcategory": product.get("subcategory"),
                "Stock Availability": product.get("stock_status", "In Stock"),
                "Care Instructions": "Dry Clean Only for best longevity",
                "Authenticity": "100% Original Brand Assured"
            }
            import pandas as pd
            st.table(pd.DataFrame(list(spec_data.items()), columns=["Attribute", "Details"]))

# ==============================================================================
# PAGE 4: HOME / CATALOG DASHBOARD (Flipkart style with categories & card view)
# ==============================================================================
else:
    # 1. Fetch Categories Summary from Backend
    cat_res = fetch_api("/api/categories")
    categories_data = cat_res.json() if cat_res and cat_res.status_code == 200 else []

    all_categories = ["All"] + [c["category"] for c in categories_data]

    # Category Bar (Flipkart Style Icons & Navigation)
    cat_cols = st.columns(len(all_categories))
    cat_icons = {
        "All": "🌟",
        "Saree": "🥻",
        "Dress Material": "👗",
        "Dress": "✨",
        "Cotton Dress": "🌸"
    }

    for idx, cat_name in enumerate(all_categories):
        with cat_cols[idx]:
            icon = cat_icons.get(cat_name, "🛍️")
            is_active = (st.session_state.selected_category == cat_name)
            btn_type = "primary" if is_active else "secondary"
            if st.button(f"{icon} {cat_name}", key=f"cat_btn_{cat_name}", type=btn_type, use_container_width=True):
                st.session_state.selected_category = cat_name
                st.session_state.selected_subcategory = "All"
                st.rerun()

    # 2. Dynamic Subcategory Tabs / Pills based on Selected Category
    subcategories = ["All"]
    if st.session_state.selected_category != "All":
        # Find subcategories for this category
        for c in categories_data:
            if c["category"] == st.session_state.selected_category:
                subcategories.extend(c.get("subcategories", []))
                break
    else:
        # Collect all subcategories across categories
        all_subs = set()
        for c in categories_data:
            for s in c.get("subcategories", []):
                all_subs.add(s)
        subcategories.extend(sorted(list(all_subs)))

    # Display Subcategory Pills / Dropdown
    subcat_col1, subcat_col2, subcat_col3 = st.columns([3, 1.5, 1.5])
    with subcat_col1:
        selected_sub = st.selectbox(
            f"📌 Filter Subcategory ({st.session_state.selected_category}):",
            options=subcategories,
            index=subcategories.index(st.session_state.selected_subcategory) if st.session_state.selected_subcategory in subcategories else 0
        )
        if selected_sub != st.session_state.selected_subcategory:
            st.session_state.selected_subcategory = selected_sub
            st.rerun()

    with subcat_col2:
        sort_by = st.selectbox(
            "⚡ Sort By:",
            options=[
                ("Popularity", "relevance"),
                ("Price -- Low to High", "price_asc"),
                ("Price -- High to Low", "price_desc"),
                ("Customer Rating", "rating_desc"),
                ("Discount", "discount_desc"),
                ("Newest First", "newest")
            ],
            format_func=lambda x: x[0]
        )

    with subcat_col3:
        max_price_filter = st.slider("Max Price (₹)", min_value=500, max_value=25000, value=25000, step=500)

    # 3. Fetch Filtered Products from FastAPI
    query_params = {
        "limit": 100,
        "max_price": max_price_filter
    }
    if st.session_state.selected_category != "All":
        query_params["category"] = st.session_state.selected_category
    if st.session_state.selected_subcategory != "All":
        query_params["subcategory"] = st.session_state.selected_subcategory
    if st.session_state.search_query.strip():
        query_params["search"] = st.session_state.search_query.strip()
    if sort_by:
        query_params["sort_by"] = sort_by[1]

    products_res = fetch_api("/api/products", data=query_params)
    products = products_res.json() if products_res and products_res.status_code == 200 else []

    # Display Results Count
    search_hint = f" for '{st.session_state.search_query}'" if st.session_state.search_query else ""
    st.markdown(f"Showing **{len(products)} products** in **{st.session_state.selected_category}** > **{st.session_state.selected_subcategory}**{search_hint}")

    if not products:
        st.warning("No products match the selected criteria. Try selecting 'All' or clearing filters.")
    else:
        # Flipkart 4-Column Grid View
        cols_per_row = 4
        for i in range(0, len(products), cols_per_row):
            row_items = products[i:i + cols_per_row]
            grid_cols = st.columns(cols_per_row)
            
            for j, item in enumerate(row_items):
                with grid_cols[j]:
                    card_placeholder = st.container()
                    with card_placeholder:
                        # Image
                        img_url = item.get("primary_image")
                        if not img_url and item.get("image_urls"):
                            img_url = item["image_urls"][0]

                        price = item.get("price", 0)
                        mrp = item.get("mrp", price * 1.5)
                        discount = item.get("discount_pct", 35)
                        rating = item.get("rating", 4.3)
                        reviews = item.get("reviews_count", 120)

                        st.markdown(f"""
                        <div class="product-card">
                            <div class="product-img-wrapper">
                                <img src="{img_url}" alt="{item.get('title')}">
                            </div>
                            <div class="product-title" title="{item.get('title')}">{item.get('title')}</div>
                            <div class="product-subcategory">{item.get('subcategory')}</div>
                            <div>
                                <span class="rating-badge">{rating} ★</span>
                                <span class="review-count">({reviews})</span>
                            </div>
                            <div class="price-row">
                                <span class="selling-price">₹{price:,.0f}</span>
                                <span class="mrp-price">₹{mrp:,.0f}</span>
                                <span class="discount-pct">{discount}% off</span>
                            </div>
                            <div class="offer-tag">Free delivery</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        btn_c1, btn_c2 = st.columns([1.5, 1])
                        with btn_c1:
                            if st.button("🔍 View Details", key=f"view_{item.get('id')}", use_container_width=True, type="primary"):
                                navigate_to("detail", product_id=item.get("id"))
                        with btn_c2:
                            if st.button("🛒 Add", key=f"quick_add_{item.get('id')}", use_container_width=True):
                                st.session_state.cart.append(item)
                                st.toast(f"Added to cart!", icon="🛒")
                                st.rerun()

st.markdown("""
<div style="text-align: center; color: #878787; font-size: 12px; margin-top: 40px; padding: 20px 0; border-top: 1px solid #e0e0e0;">
    <b>AKKI LATEST COLLECTIONS</b> © 2026. Built with Python, FastAPI, MySQL & Streamlit UI.
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# FLOATING RIGHT-BOTTOM COMPANY POLICY CHATBOT (RAG + OPENAI)
# ==============================================================================
# FLOATING RIGHT-BOTTOM COMPANY POLICY CHATBOT (RAG + OPENAI)
# ==============================================================================
# FLOATING RIGHT-BOTTOM COMPANY POLICY CHATBOT (RAG + OPENAI)
# ==============================================================================
# FLOATING RIGHT-BOTTOM AKKI USER GUIDE (SHOPPING & PRODUCT ASSISTANT)
# ==============================================================================
# FLOATING RIGHT-BOTTOM AKKI USER GUIDE (SHOPPING & PRODUCT ASSISTANT)
# ==============================================================================
def render_right_bottom_chatbot():
    """Renders the fixed bottom-right AKKI User Guide & Shopping Assistant widget."""
    effective_key = OPENAI_API_KEY
    effective_model = OPENAI_MODEL
    
    col_spacer, col_bot = st.columns([8, 2])
    with col_bot:
        with st.popover("🎧 Ask AKKI", use_container_width=False):
            # 1. Sticky Header Bar with Title Banner (matching bottom button gradient, clear button removed)
            st.markdown("""
            <div class="chat-sticky-header">
                <div class="chat-top-banner">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 20px;">🛍️</span>
                            <span class="chat-top-title" style="font-size: 16px; font-weight: 700; color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; letter-spacing: 0.3px;">AKKI User Guide</span>
                        </div>
                        <span class="chat-online-badge">● ONLINE</span>
                    </div>
                    <div class="chat-top-subtitle" style="font-size: 11px; color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; margin-top: 4px; font-weight: 400; letter-spacing: 0.2px;">
                        Personal Shopping Assistant & Product Catalog Guide
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 2. Frequently Asked Questions (Compact quick chips)
            st.markdown("<div style='font-size: 11px; font-weight: 600; color: #64748b; margin: 6px 0 4px 0;'>💡 Frequently Asked Questions:</div>", unsafe_allow_html=True)
            q1, q2 = st.columns(2)
            with q1:
                if st.button("🥻 Available Sarees?", key="quick_q1", use_container_width=True):
                    st.session_state.pending_policy_query = "What saree varieties, fabrics, and subcategories are available in your collection?"
            with q2:
                if st.button("👗 Dress Materials?", key="quick_q2", use_container_width=True):
                    st.session_state.pending_policy_query = "What types of unstitched dress materials and suit sets do you offer?"
            
            q3, q4 = st.columns(2)
            with q3:
                if st.button("✨ Ready Dresses?", key="quick_q3", use_container_width=True):
                    st.session_state.pending_policy_query = "What ready-to-wear dresses, Anarkali suits, and gowns are available?"
            with q4:
                if st.button("🚚 Delivery & Returns?", key="quick_q4", use_container_width=True):
                    st.session_state.pending_policy_query = "What are the shipping charges, delivery times, and 7-day replacement policies?"

            st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #f1f5f9;'>", unsafe_allow_html=True)

            # 3. Clean Chat Message History
            for msg in st.session_state.policy_chat_history:
                with st.chat_message(msg["role"], avatar="🧑‍💼" if msg["role"] == "user" else "🛍️"):
                    st.markdown(msg["content"])

            # Flexible spacer ensuring input box is always pushed to bottom
            st.markdown('<div class="chat-flex-spacer"></div>', unsafe_allow_html=True)

            # 4. Sticky Bottom Input Form (Fixed at the bottom of the popover view)
            with st.form("policy_chat_form", clear_on_submit=True):
                in_c1, in_c2 = st.columns([3.8, 1.2])
                with in_c1:
                    user_text = st.text_input(
                        "Ask question:",
                        placeholder="Ask your question...",
                        label_visibility="collapsed",
                        key="policy_user_input_field"
                    )
                with in_c2:
                    submitted = st.form_submit_button("Send 🚀", use_container_width=True)

            # 5. Query Processing
            query_to_process = None
            if submitted and user_text and user_text.strip():
                query_to_process = user_text.strip()
            elif st.session_state.pending_policy_query:
                query_to_process = st.session_state.pending_policy_query
                st.session_state.pending_policy_query = None

            if query_to_process:
                st.session_state.policy_chat_history.append({
                    "role": "user",
                    "content": query_to_process,
                    "sources": []
                })
                
                with st.spinner("Searching..."):
                    engine = get_rag_engine()
                    conv_history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.policy_chat_history[:-1]
                    ]
                    res = engine.answer_query(
                        query=query_to_process,
                        conversation_history=conv_history,
                        api_key=effective_key,
                        model=effective_model
                    )
                    
                    st.session_state.policy_chat_history.append({
                        "role": "assistant",
                        "content": res.get("answer", "No response could be generated."),
                        "sources": res.get("sources", [])
                    })
                
                st.rerun()

# Mount the floating right-bottom chatbot across the application
render_right_bottom_chatbot()
