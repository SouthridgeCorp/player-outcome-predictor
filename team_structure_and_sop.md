# Team Structure for the project

## Sponsors/Stakeholders:
- Responsible for giving structured feedback when the team asks for it
- Provides `budget` for the project

### People:
`list_of_stakeholders`

## Target User Personas:
- Responsible for using a deployed major version release in line with the expected user experience
- Responsible for using the in-app feedback loop to influence the roadmap for subsequent releases

### People:
`list_of_users_by_target_user_persona`

## Controller:
- Responsible for:
  - Stakeholder management
  - Release Planning
  - Milestone Planning
  - Code Review
  - Enforcement of the right level of SDLC
  - Team Staffing
  - Budget control and alerting

### People:
`list_of_controllers`

## Executor:
- Responsible for:
  - Issue Planning
  - Giving feedback on Release/Milestone planning when required
  - Code Implementation for Issues
  - Adhering to SDLC as per the needs of the project
  - Code Review for other Executors

### People:
`list_of_executors`

## Understudy:
- Responsible for:
  - Shadow everything that is going on
  - Proactively ask questions if they don't understand what is going on
  - Learn the workflows of the Executor and the Controller so that they can provide support in case execution is at risk

### People:
`list_of_understudies`

## Team Graph

```mermaid
graph TD

    sponsor -->|provides| budget
    sponsor -->|provides| feedback_form
    `list_of_sponsors` --> |is| sponsor
    
    controller -->|seeks| feedback
    controller --> |controls| budget
    controller --> |plans| milestone_v_maj.1
    controller --> |plans| milestone_v_maj.x
    controller --> |plans| release_v_maj+1
    controller --> |allocates| executor
    controller --> |allocates| understudy
    controller --> |reviews| code
    controller --> |also_is| executor
    controller --> |imposes| SDLC
    `list_of_controllers` --> |is| controller
    
    
    executor --> |provides| feedback
    executor --> |writes| code
    executor --> |adheres_to| SDLC
    `list_of_executors` --> |is| executor
    
    understudy --> |shadows| controller
    understudy --> |shadows| executor
    understudy --> |provides| feedback
    `list_of_understudies` --> |is| understudy
    
    target_user_persona --> |uses| release_v_maj+1
    target_user_persona --> |uses| feedback_form
    `list_of_users_by_target_user_persona` --> |is| target_user_persona

    feedback --> |applies_to| release_v_maj+1
    budget --> |allocated_to| release_v_maj+1
    
    release_v_maj+1 --> |includes| milestone_v_maj.1
    release_v_maj+1--> |includes| milestone_v_maj.x
    
    milestone_v_maj.1 --> |includes| working_backwards
    milestone_v_maj.1 --> |informs| milestone_v_maj.x

    working_backwards --> |informs| press_release
    working_backwards --> |informs| faq
    working_backwards --> |includes| customer
    working_backwards --> |includes| opportunity
    working_backwards --> |includes| benefit
    working_backwards --> |includes| user_experience
    
    opportunity --> |informs| computational_model
    opportunity --> |informs| benefit
    benefit --> |informs| computational_model
    customer --> |informs| target_user_persona
    target_user_persona --> |informs| feedback_form
    target_user_persona --> |informs| user_experience
    target_user_persona --> |informs| opportunity
    target_user_persona --> |informs| benefit
    target_user_persona --> |informs| validation
    opportunity --> |informs| user_experience
    benefit --> |informs| user_experience
    user_experience --> |informs| architecture_hypothesis
    user_experience --> |informs| feedback_form
    
    press_release --> |provides| conviction
    faq --> |provides| conviction
    validation --> |provides| conviction
    feedback --> |provides| conviction
    conviction --> |justifies| budget
    
    
    computational_model --> |informs| architecture_hypothesis
    feedback_form --> |collects| feedback    
    computational_model --> |informs| milestone_v_maj.x
    architecture_hypothesis --> |informs| milestone_v_maj.x
        
    milestone_v_maj.x --> |includes| code_issue
    code_issue --> |resolved_by| code
    SDLC --> |applies_to| milestone_v_maj.x

    subgraph roles
    sponsor
    controller
    executor
    understudy 
    target_user_persona
    end
    
    subgraph people
    `list_of_sponsors`
    `list_of_controllers`
    `list_of_executors`
    `list_of_understudies`
    `list_of_users_by_target_user_persona`
    end
    
    subgraph responsibilities
    feedback
    budget
    conviction
    end
    
    subgraph PR_FAQ
    working_backwards
    customer
    opportunity
    benefit
    validation
    user_experience
    press_release
    faq
    feedback_form
    end
    
    subgraph architecture
    computational_model
    architecture_hypothesis
    end
    
    subgraph release_plan
    release_v_maj+1
    milestone_v_maj.1
    milestone_v_maj.x
    code_issue
    code
    SDLC

    end
    
    style roles fill:#8a824c,stroke:#333,stroke-width:4px
    style responsibilities fill:#4c8a75,stroke:#333,stroke-width:4px
    style people fill:#508a4c,stroke:#333,stroke-width:4px
    style PR_FAQ fill:#99CCFF,stroke:#333,stroke-width:4px
    style architecture fill:#FF99FF,stroke:#333,stroke-width:4px
    style release_plan fill:#339999,stroke:#333,stroke-width:4px

```
