# CCA Industry Council Survey

This repository contains two versions of the CCA Industry Council Pre-Workshop Survey:

1. **Command-line version** (`app.py`) - Uses OpenAI agents for intelligent conversation
2. **Streamlit version** (`streamlit_app.py`) - Modern web interface with chat component

## Setup

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation

1. **Clone or download this repository**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Running the Applications

### Option 1: Streamlit Web App (Recommended)

The Streamlit version provides a modern, user-friendly web interface with the latest chat component.

```bash
streamlit run streamlit_app.py
```

**Features:**
- 🎨 Modern web interface
- 💬 Interactive chat component
- 📱 Responsive design
- 📊 Real-time progress tracking
- 📥 JSON export functionality
- 🔄 Survey reset capability

### Option 2: Command-line AI Agent

The command-line version uses OpenAI agents for intelligent conversation and adaptive questioning.

```bash
python app.py
```

**Features:**
- 🤖 AI-powered conversation
- 🧠 Intelligent question flow
- 🔄 Adaptive follow-up questions
- 📝 Structured data output

## Survey Structure

Both versions include the same CCA Industry Council survey questions:

### Question 1: Biggest Challenge
- **Main Question**: Which of the five trends poses the biggest challenge?
  - Return to customer care
  - The super powered customer
  - Regulation for good
  - Rise of the conscious consumer
  - The agent of the future

- **Follow-up**: Why is this the biggest challenge?
  - Financial impact
  - Workforce impact
  - Skills and capability implications
  - Organisational strategy implications
  - Something else

- **Readiness**: Current organisational readiness level

### Question 2: Most Challenging Persona
- **Main Question**: Which persona is most challenging to satisfy?
  - 🔮 Future Customer
  - 👥 Future Frontline Worker
  - 🧠 Future Leader

- **Follow-up**: Biggest factor influencing this challenge

### Question 3: Positive Impact
- **Open-ended**: What factor would have the biggest positive impact?

## Output

Both applications generate structured JSON output with all survey responses, suitable for analysis and workshop planning.

## Usage Notes

- The Streamlit version is recommended for most users due to its intuitive interface
- The command-line version is useful for testing and development
- Both versions maintain the exact wording and structure specified by CCA
- All responses are validated and formatted consistently

## Support

For questions or issues, please refer to the CCA Industry Council documentation or contact the development team.
