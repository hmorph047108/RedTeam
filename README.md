# Strategic Red Team Analyzer

A comprehensive strategy analysis tool that uses multiple Claude Opus 4 perspectives to provide thorough red team analysis of strategic plans, business ideas, and proposals.

## Features

### 🎯 Core Functionality
- **Multi-perspective Analysis**: Analyze strategies from 7 different analytical perspectives
- **Mental Model Integration**: Apply proven cognitive frameworks to strengthen analysis
- **Chained AI Analysis**: Uses multiple Claude Opus 4 API calls for comprehensive insights
- **Interactive Results**: Collapsible sections with confidence scores and detailed insights
- **Export Capabilities**: Save analysis to PDF, Markdown, or JSON formats

### 🔍 Red Team Perspectives

1. **😈 Devil's Advocate** - Aggressive challenge of assumptions and weaknesses
2. **🔄 Systems Thinker** - Analyze interconnections, feedback loops, unintended consequences
3. **📚 Historical Analyst** - Compare to past similar strategies/failures
4. **👥 Stakeholder Advocate** - Represent different stakeholder concerns
5. **⚠️ Risk Assessment** - Identify failure modes and mitigation strategies
6. **💰 Resource Realist** - Challenge feasibility and resource requirements
7. **📈 Market Forces** - Competitive and economic pressures analysis

### 🧠 Mental Model Frameworks

- **First Principles Thinking** - Break down to fundamental components
- **Inversion** - Focus on what could go wrong
- **Second/Third Order Effects** - Analyze consequences of consequences
- **Opportunity Cost Analysis** - What alternatives are being foregone
- **Base Rate Neglect** - Historical success rates for similar strategies
- **Confirmation Bias Detection** - Identify overlooked contradictory evidence
- **Strategic Options Theory** - View strategy as creating future options

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hmorph047108/RedTeam.git
   cd RedTeam
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Anthropic API key
   ```

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```

## Configuration

### API Key Setup

**Option 1: OpenRouter (Recommended for Claude Opus 4)**
- Get an OpenRouter API key from [openrouter.ai](https://openrouter.ai)
- Add to your `.env` file:
  ```
  OPENROUTER_API_KEY=your_openrouter_api_key_here
  USE_OPENROUTER=true
  OPENROUTER_SITE_URL=your_site_url_here
  OPENROUTER_SITE_NAME=Strategic Red Team Analyzer
  ```

**Option 2: Direct Anthropic API**
- Get your Anthropic API key from [console.anthropic.com](https://console.anthropic.com)
- Add it to your `.env` file:
  ```
  ANTHROPIC_API_KEY=your_anthropic_api_key_here
  USE_OPENROUTER=false
  ```
- Or enter it in the application sidebar

### Application Settings
- **Concurrent Analyses**: Adjust number of parallel API requests (1-3)
- **Response Length**: Configure maximum tokens per analysis (2000-6000)
- **Analysis Creativity**: Control temperature for AI responses (0.0-1.0)

## Usage

1. **Enter Your Strategy**: Describe your strategy, business plan, or idea in the text area
2. **Select Perspectives**: Choose which analytical perspectives to apply from the sidebar
3. **Choose Mental Models**: Select cognitive frameworks to enhance the analysis
4. **Run Analysis**: Click "Start Red Team Analysis" to begin
5. **Review Results**: Examine detailed analysis from each perspective
6. **Generate Synthesis**: Create unified insights and recommendations
7. **Export Results**: Save your analysis in PDF, Markdown, or JSON format

## Example Use Cases

- **Business Strategy Validation**: Test business plans against multiple analytical lenses
- **Product Launch Planning**: Identify risks and assumptions in go-to-market strategies
- **Investment Decisions**: Analyze investment opportunities from various perspectives
- **Project Proposals**: Strengthen project plans by identifying weaknesses
- **Policy Analysis**: Evaluate policy proposals for unintended consequences
- **Crisis Planning**: Test crisis response strategies for robustness

## Technical Architecture

### Core Components
- **`app.py`**: Main Streamlit application and UI orchestration
- **`red_team_analyzer.py`**: Core analysis engine with async API calls
- **`prompts.py`**: Perspective-specific prompts and mental model frameworks
- **`ui_components.py`**: Modular UI components and visualizations
- **`export_utils.py`**: PDF and Markdown export functionality
- **`utils.py`**: Utility functions and validation logic

### Key Features
- **Async Processing**: Concurrent API calls for improved performance
- **Progress Tracking**: Real-time progress indicators during analysis
- **Error Handling**: Comprehensive error handling with retry logic
- **Rate Limiting**: Respects API rate limits with intelligent delays
- **Caching**: Streamlit caching for improved performance

## Development

### Project Structure
```
RedTeam/
├── app.py                 # Main Streamlit application
├── red_team_analyzer.py   # Core analysis engine
├── prompts.py            # AI prompts and frameworks
├── ui_components.py      # UI components
├── export_utils.py       # Export functionality
├── utils.py              # Utility functions
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

### Adding New Perspectives
1. Add perspective configuration to `config.py`
2. Create prompts in `prompts.py`
3. Update UI components if needed
4. Test with various strategy inputs

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Security & Privacy

- **API Key Security**: API keys are handled securely and not stored
- **Data Privacy**: No strategy data is stored or transmitted beyond Anthropic's API
- **Input Validation**: Strategy inputs are validated for security
- **Export Security**: Exported files contain only your analysis data

## Limitations

- **API Costs**: Each analysis uses multiple Claude Opus 4 API calls
- **Rate Limits**: Respect Anthropic's API rate limits
- **Analysis Quality**: Output quality depends on strategy description detail
- **Language**: Currently optimized for English language strategies

## Troubleshooting

### Common Issues

**"Invalid API Key" Error**
- Verify your Anthropic API key format
- Ensure you have sufficient API credits
- Check for typos in the API key

**Analysis Takes Too Long**
- Reduce number of selected perspectives
- Check your internet connection
- Verify API rate limits aren't exceeded

**Export Fails**
- Ensure you have completed an analysis first
- Check file permissions for downloads
- Try a different export format

**Low Confidence Scores**
- Provide more detailed strategy descriptions
- Include specific context and constraints
- Consider the complexity of your strategy

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the example use cases

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for the web interface
- Powered by [Anthropic's Claude Opus 4](https://www.anthropic.com/) for analysis
- Uses [Plotly](https://plotly.com/) for visualizations
- PDF generation with [ReportLab](https://www.reportlab.com/)

---

**⚠️ Disclaimer**: This tool provides analytical perspectives to enhance strategic thinking. It should complement, not replace, human judgment and domain expertise. Always validate insights with subject matter experts and real-world testing.