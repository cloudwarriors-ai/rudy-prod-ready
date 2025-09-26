# Auto Attendant Parameter Analysis

## Provided Parameters Analysis

### Audio Prompt
- **ID**: "" (empty - will use default)
- **Name**: "Default"
- **Mapping**: Text-to-speech prompt

### Key Actions Analysis

1. **Key "0"**: 
   - Action: 100 (likely "Transfer to Queue/User")
   - Target: Rudy - MS Teams ETL (extension 999052)
   - Has voicemail greeting configuration

2. **Key "1"**:
   - Action: 2 (likely "Transfer to User")
   - Target: John Rudolph (extension 999023)

3. **Key "2"**:
   - Action: 2 (likely "Transfer to User") 
   - Target: Tyler Pratt (extension 625)

4. **Key "3"**:
   - Action: 7 (likely "Transfer to Extension/User")
   - Target: Opencode-Tyler (extension 13245)

5. **Key "4"**:
   - No action defined (empty option)

6. **Key "*"**:
   - Action: 21 (likely "Repeat menu" or "Return to main menu")

### Caller No Action
- Action: -1 (likely "Timeout/Default")
- Audio prompt repeat: 3 times

## Action Code Mapping (Assumed)
- Action 2: Transfer to User
- Action 7: Transfer to User/Extension  
- Action 21: Repeat Menu
- Action 100: Transfer to Queue/Group
- Action -1: Timeout/Disconnect

## Teams Mapping Strategy
1. Create prompts for greetings and menu
2. Create callable entities for each target user
3. Create menu options for each key press
4. Configure timeout behavior
5. Build complete Auto Attendant structure