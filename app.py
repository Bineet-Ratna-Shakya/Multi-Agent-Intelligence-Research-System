# Streamlit UI

import streamlit as st
import json
import os
import traceback
from datetime import datetime
from agents.coordinator_agent import CoordinatorAgent
from utils.logger import setup_logger
from config import PRODUCT_CATEGORIES

st.set_page_config(
    page_title="Competitive Intelligence System",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.coordinator = None
    st.session_state.last_query = ""
    st.session_state.last_category = "ai_productivity"

@st.cache_resource
def setup_logging():
    try:
        os.makedirs("logs", exist_ok=True)
        return setup_logger("WebApp", "logs/webapp.log")
    except Exception as e:
        st.error(f"Failed to setup logging: {e}")
        return None

logger = setup_logging()

@st.cache_resource
def get_coordinator():
    try:
        os.makedirs("reports", exist_ok=True)
        coordinator = CoordinatorAgent()
        return coordinator
    except Exception as e:
        st.error(f"Failed to initialize coordinator: {e}")
        if logger:
            logger.error(f"Failed to initialize coordinator: {e}")
        return None

def run_analysis(query, category_tuple, output_format):
    try:
        coordinator = get_coordinator()
        if not coordinator:
            return False, "Failed to initialize the system"
        
        task = {
            "query": query.strip(),
            "product_category": category_tuple[0]
        }
        
        result = coordinator.execute(task)
        
        if result["success"]:
            return True, result
        else:
            error_msg = result.get("error", "Unknown error occurred")
            return False, error_msg
            
    except Exception as e:
        error_msg = f"System error: {str(e)}"
        if logger:
            logger.error(f"Analysis failed: {error_msg}\n{traceback.format_exc()}")
        return False, error_msg

def main():
    st.title("Multi-Agent Competitive Intelligence System")
    st.markdown("**Discover the latest product updates using AI agents - Made by Bineet Shakya.**")
    st.divider()
    
    with st.sidebar:
        st.header("Query Configuration")
        
        query = st.text_area(
            "Search Query",
            value=st.session_state.get('query_input', ''),
            placeholder="e.g., 'iPhone 16 features' or 'ChatGPT updates'",
            help="Enter your search query",
            key="query_input"
        )
        
        category_options = [
            ("ai_productivity", "AI Productivity Tools"),
            ("devops_platforms", "DevOps Platforms"), 
            ("consumer_electronics", "Consumer Electronics")
        ]
        
        default_index = 0
        try:
            if 'category_selection' in st.session_state:
                for i, (key, _) in enumerate(category_options):
                    if key == st.session_state.category_selection:
                        default_index = i
                        break
        except:
            default_index = 0
        
        category = st.selectbox(
            "Product Category",
            options=category_options,
            index=default_index,
            format_func=lambda x: x[1],
            help="Select the product category that best matches your query",
            key="category_selection"
        )
        
        output_format = st.radio(
            "Output Format",
            options=["markdown", "json"],
            index=0,
            help="Choose the format for the downloadable report"
        )
        
        analyze_button = st.button(
            "Run Analysis",
            type="primary",
            use_container_width=True,
            disabled=not query.strip()
        )
        
    
    if analyze_button and query.strip():
        with st.spinner("Searching and analyzing content... This may take TimmmeeEeEeEeEeeee."):
            
            success, result_data = run_analysis(query, category, output_format)
            
            if success:
                report = result_data["report"]
                stats = result_data["stats"]
                
                tab1, tab2, tab3 = st.tabs(["Summary", "Details", "Download"])
                
                with tab1:
                    st.subheader("Analysis Summary")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Sources Found", stats.get('sources_found', 0))
                    with col2:
                        st.metric("Summaries Generated", stats.get('summaries_generated', 0))
                    with col3:
                        st.metric("Summaries Verified", stats.get('summaries_verified', 0))
                    with col4:
                        st.metric("Products Found", report.get('summary', {}).get('products_mentioned', 0))
                    
                    st.divider()
                    
                    st.markdown(f"""
                    **Query**: {query}  
                    **Category**: {category[1]}  
                    **Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
                    **Total Updates Found**: {report.get('summary', {}).get('total_updates_found', 0)}
                    """)
                
                with tab2:
                    st.subheader("Product Updates")
                    
                    updates = report.get("updates", [])
                    if updates:
                        for i, update in enumerate(updates, 1):
                            with st.expander(f"{i}. {update.get('product', 'Unknown Product')}", expanded=True):
                                st.markdown(f"**Summary**: {update.get('summary', 'No summary available')}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown(f"**Date**: {update.get('date', 'Unknown')}")
                                with col2:
                                    source_url = update.get('source', '#')
                                    if source_url and source_url != '#':
                                        st.markdown(f"**Source**: [View Source]({source_url})")
                                    else:
                                        st.markdown("**Source**: Not available")
                    else:
                        st.info("No product updates found. Try a different query or category.")
                
                with tab3:
                    st.subheader("Download Report")
                    
                    try:
                        coordinator = get_coordinator()
                        if coordinator:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            query_safe = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
                            query_safe = query_safe.replace(" ", "_")[:20]
                            filename = f"competitive_intelligence_{query_safe}_{timestamp}"
                            
                            filepath = coordinator.save_report(report, format=output_format, filename=filename)
                            
                            with open(filepath, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            
                            st.download_button(
                                label=f"Download {output_format.upper()} Report",
                                data=file_content,
                                file_name=f"{filename}.{output_format}",
                                mime="application/json" if output_format == "json" else "text/markdown"
                            )
                            
                            st.success(f"Report saved successfully: {filepath}")
                        else:
                            st.error("Could not save report - system initialization failed")
                            
                    except Exception as e:
                        st.error(f"Error saving report: {str(e)}")
                        if logger:
                            logger.error(f"Error saving report: {str(e)}")
            else:
                st.error(f"Analysis failed: {result_data}")
    
    elif analyze_button and not query.strip():
        st.warning("Please enter a search query")
    
    if not analyze_button or not query.strip():
        st.info("Enter a query in the sidebar and click 'Run Analysis' to start")
        
        st.subheader("System Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Agent Pipeline:**
            1. **SearchAgent** - Web search & content extraction
            2. **SummarizerAgent** - Content analysis (BART model)
            3. **VerifierAgent** - Quality verification 
            4. **CoordinatorAgent** - Pipeline orchestration
            """)
        
        with col2:
            st.markdown("""
            **Features:**
            - Multi-source web search (news, blogs, official sites)
            - AI-powered content summarization
            - PDF document support
            - Source diversity and verification
            - Local Hugging Face models (offline operation)
            """)
        
        st.subheader("System Status")
        coordinator = get_coordinator()
        if coordinator:
            st.success("System initialized successfully")
        else:
            st.error("System initialization failed")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.error("Please refresh the page and try again.")
        if logger:
            logger.error(f"Application error: {str(e)}\n{traceback.format_exc()}")