# Conference Bot Implementation Plan

## Overview
Create a new conversational bot for conference preparation that follows the provided script structure. The bot will collect information about conference attendees' sectors, challenges, and planning status to help shape conference content.

## Bot Flow Analysis

### 1. Initial Greeting & Introduction
- **Input**: User name
- **Bot Response**: Personalised greeting with bot name introduction
- **Purpose**: Establish rapport and set context for the conversation

### 2. Context Setting
- Explain the purpose: understanding challenges and planning status
- Emphasise confidentiality and collective feedback value
- Set expectations for the conversation

### 3. Sector Identification
**Primary Question**: "Which sector do you work in?"

**Sector Options** (with keyword matching):
1. **Retail & E-commerce** - Keywords: retail, order support, bookings, returns, product enquiries, loyalty programs, online orders
2. **Financial Services** - Keywords: banking, banking queries, fraud, fraud detection, loans, applications, insurance, claims, mortgages, investments, Building Societies
3. **Telecommunications** - Keywords: telecoms, billing, billing queries, technical support, service upgrades, mobiles, services, broadband, internet
4. **Utilities** - Keywords: account management, outage reporting, billing, payments, water, gas, electricity, domestic, oil, hardship
5. **Public Sector & Government** - Keywords: benefits, benefit support, tax, tax enquiries, local council services, NHS helplines, NHS 111, Housing, Housing Associations
6. **Healthcare** - Keywords: appointment booking, prescription queries, patient support, private medical insurance, care homes, elderly care
7. **Travel & Hospitality** - Keywords: travel bookings, travel cancellations, loyalty programmes, airline, hotels, accommodation, trains, bus operators, highways agencies, waterways
8. **Education** - Keywords: new admissions, universities, student support, alumni services, schools, primary, secondary, clearing
9. **Technology & IT** - Keywords: software, hardware, PC, IT support, technical support, service desk, licence management, subscription management
10. **Media & Entertainment** - Keywords: subscription services, content access issues, films, sport, cinema, theatre, booking, pay per view, games, gaming
11. **Outsourcing & BPO** - Keywords: offshore, 3rd Party, onshore
12. **Charities & non profits** - Keywords: donation support, volunteer co-ordination, helpline services
13. **Debt collection** - Keywords: payment reminders, account resolution, financial support, distress, hardship
14. **Emergency services** - Keywords: police, fire service, ambulance service, motoring service, coastguard

**Intelligent Matching Logic**:
- Exact sector name match (RED text) takes priority
- Keyword matching (BLACK text) for partial matches
- Multiple suggestions if multiple keywords match
- Confirmation step before proceeding

### 4. Challenge Identification (Headwinds)
**Primary Question**: "Please can you describe the key challenge you face, we call these headwinds"

**Challenge Categories** (with keyword matching):
1. **Economic volatility** - Keywords: ageing population, economy, uncertainty, financial support, distress, hardship, assistance
2. **Technology acceleration** - Keywords: self-service, human supported tech, skilled, skilling, complex conversations, cost
3. **Regulatory priorities** - Keywords: positive regulation, driving better customer outcomes, reduce customer harm, evidence, audit, auditing, payment process, regulation for good
4. **Sustainability agenda** - Keywords: reduce energy costs, reduce carbon emissions, environmental impact, customer environmental buying choices, society
5. **Shifting workplace realities** - Keywords: multi-generational workplaces, geographically diverse skill bases, recruitment challenges, pay expectations, automation, recruitment, training and development, talent retention, agents

**Intelligent Matching Logic**:
- Exact challenge name match (RED text) takes priority
- Keyword matching (BLACK text) for partial matches
- Multiple suggestions if multiple keywords match
- Confirmation step before proceeding

### 5. Planning Status Assessment
**Primary Question**: "How far down the road are you with planning and implementing a solution to the headwinds identified?"

**Scale**: 0-10 where:
- 0-4: Preparation and planning
- 5-10: Execution

**Follow-up Questions**:
- **If 0-4**: "Can you describe your challenge in more detail?" (up to XXXX characters)
- **If 5-10**: "Can you describe your challenge and your resolution plan in detail?" (up to XXXX characters), including end-to-end timeline

### 6. Additional Insights
**Question**: "Just whilst we have been talking, is there anything else you have thought which you think may be relevant?"

**Input**: Free text (up to XXXX characters)

### 7. Closing
- Thank the participant
- Express anticipation for conference attendance

## Data Collection Requirements

The bot should capture:
1. **Participant Name** - For personalisation
2. **Sector** - From the 14 defined sectors
3. **Key Challenge** - From the 5 headwind categories
4. **Planning Status** - 0-10 scale
5. **Challenge Description** - Detailed text based on planning status
6. **Resolution Plan** - If in execution phase (5-10)
7. **Timeline** - How long to resolve (if in execution phase)
8. **Additional Insights** - Free text input

## Technical Implementation Plan

### Phase 1: Core Bot Structure
1. Create new bot file (`conference_bot.py`)
2. Implement conversation flow management
3. Add intelligent keyword matching system
4. Create data validation and storage

### Phase 2: Sector & Challenge Matching
1. Implement sector keyword matching logic
2. Implement challenge (headwind) keyword matching logic
3. Add confirmation mechanisms for ambiguous matches
4. Handle multiple suggestion scenarios

### Phase 3: Data Collection & Validation
1. Implement planning status scale (0-10)
2. Add conditional follow-up questions
3. Implement character limits for text inputs
4. Add data validation and error handling

### Phase 4: User Interface
1. Create Streamlit interface for the conference bot
2. Implement chat-style interaction
3. Add progress indicators
4. Create results summary and export functionality

### Phase 5: Testing & Refinement
1. Test all conversation flows
2. Validate keyword matching accuracy
3. Test edge cases and error handling
4. Refine user experience based on testing

## Key Features to Implement

### Intelligent Matching System
- **Exact Match Priority**: Direct sector/challenge name matches
- **Keyword Matching**: Partial matches using defined keywords
- **Multiple Suggestions**: When multiple categories match
- **Confirmation Flow**: Always confirm before proceeding

### Conversation Management
- **State Tracking**: Track conversation progress
- **Context Awareness**: Remember previous answers
- **Error Handling**: Graceful handling of invalid inputs
- **Personalisation**: Use participant name throughout

### Data Quality
- **Validation**: Ensure data completeness and accuracy
- **Character Limits**: Enforce text input limits
- **Export Functionality**: JSON export for analysis
- **Summary Generation**: Clear summary of collected data

## Success Metrics
1. **Completion Rate**: Percentage of users who complete the full survey
2. **Data Quality**: Accuracy of sector and challenge identification
3. **User Experience**: Time to completion and user satisfaction
4. **Data Utility**: Quality of insights for conference planning

## Next Steps
1. Create the core bot implementation
2. Implement the keyword matching system
3. Build the Streamlit interface
4. Test with sample conversations
5. Refine based on testing results
6. Deploy and monitor performance

