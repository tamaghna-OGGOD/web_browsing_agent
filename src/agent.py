from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
from crewai.flow.flow import Flow, start, listen
from stage_hand_tool import browser_automation

# Streamlit for the frontend
import streamlit as st
import asyncio

# Define our LLMs for providing to agents
planner_llm = LLM(model="openai/gpt-4o")
automation_llm = LLM(model="openai/gpt-4o")
response_llm = LLM(model="openai/gpt-4o")


@tool("Stagehand Browser Tool")
def stagehand_browser_tool(task_description: str, website_url: str) -> str:
    """
    A tool that allows interaction with a web browser using Stagehand capabilities.
    
    Args:
        task_description (str): The task description for the agent to perform.
        website_url (str): The URL of the website to interact and navigate to.
    
    Returns:
        str: The result of the browser automation task.
    """
    return browser_automation(task_description, website_url)


class BrowserAutomationFlowState(BaseModel):
    """State model for the browser automation flow."""
    query: str = Field(default="", description="User's automation query")
    result: str = Field(default="", description="Final automation result")


class AutomationPlan(BaseModel):
    """Structured output model for automation planning."""
    task_description: str = Field(
        ..., 
        description="Brief description of the automation task to be performed"
    )
    website_url: str = Field(
        ..., 
        description="Target website URL for the automation task"
    )
    estimated_complexity: Optional[str] = Field(
        default="medium",
        description="Estimated complexity level: low, medium, or high"
    )


class AutomationResult(BaseModel):
    """Structured output model for automation execution results."""
    success: bool = Field(..., description="Whether the automation was successful")
    data: str = Field(..., description="Extracted or processed data from the automation")
    error_message: Optional[str] = Field(
        default=None, 
        description="Error message if automation failed"
    )
    actions_performed: Optional[str] = Field(
        default=None,
        description="Summary of actions performed during automation"
    )


class FinalResponse(BaseModel):
    """Structured output model for the final user response."""
    summary: str = Field(..., description="Brief summary of what was accomplished")
    details: str = Field(..., description="Detailed results or findings")
    recommendations: Optional[str] = Field(
        default=None,
        description="Any recommendations or next steps for the user"
    )


class BrowserAutomationFlow(Flow[BrowserAutomationFlowState]):
    """
    A CrewAI Flow to intelligently handle browser automation tasks
    through specialized agents using Stagehand tools.
    """

    @start()
    def start_flow(self) -> Dict[str, Any]:
        """Initialize the automation flow with the user's query."""
        print(f"🚀 Flow started with query: {self.state.query}")
        return {"query": self.state.query}

    @listen(start_flow)
    def plan_task(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Plan the automation task based on the user's query."""
        print("📋 Using Automation Planner to analyze the task...")

        planner_agent = Agent(
            role="Automation Planner Specialist",
            goal="Analyze user queries and create detailed automation plans",
            backstory="""You are an expert browser automation strategist with deep knowledge 
            of web technologies and automation best practices. You excel at breaking down 
            complex user requests into actionable automation tasks.""",
            llm=planner_llm,
        )

        plan_task = Task(
            description=f"""
            Analyze the following user query and create a comprehensive automation plan:
            
            User Query: '{inputs['query']}'
            
            Your task is to:
            1. Identify the target website URL from the query
            2. Define the specific automation task to be performed
            3. Assess the complexity level of the task
            4. Ensure the plan is actionable and specific
            
            If no specific URL is provided, use https://www.google.com as the default.
            """,
            agent=planner_agent,
            output_pydantic=AutomationPlan,
            expected_output="""A structured automation plan containing the task description, 
            target website URL, and estimated complexity level.""",
        )

        crew = Crew(agents=[planner_agent], tasks=[plan_task], verbose=True)
        result = crew.kickoff()

        # FIX: Access the Pydantic model through .pydantic attribute
        plan = result.pydantic  # This gets the AutomationPlan object
        
        # Ensure we have a valid website URL
        website_url = plan.website_url
        if not website_url or website_url.lower() in ["", "none", "null", "n/a"]:
            website_url = "https://www.google.com"

        return {
            "task_description": plan.task_description,
            "website_url": website_url,
            "estimated_complexity": plan.estimated_complexity,
        }

    @listen(plan_task)
    def handle_browser_automation(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the browser automation task using Stagehand."""
        print("🤖 Executing browser automation task...")

        automation_agent = Agent(
            role="Browser Automation Specialist",
            goal="Execute precise browser automation tasks using advanced AI-powered tools",
            backstory="""You are a highly skilled browser automation engineer with expertise 
            in Stagehand and modern web automation techniques. You can navigate complex websites, 
            extract data accurately, and handle dynamic web elements with precision.""",
            tools=[stagehand_browser_tool],
            llm=automation_llm,
        )

        automation_task = Task(
            description=f"""
            Execute the following browser automation task with precision:
            
            Target Website: {inputs['website_url']}
            Task Description: {inputs['task_description']}
            Estimated Complexity: {inputs.get('estimated_complexity', 'medium')}
            
            Instructions:
            1. Navigate to the specified website
            2. Perform the requested automation task
            3. Extract or process the required information
            4. Document any actions taken
            5. Handle errors gracefully and provide meaningful feedback
            
            Use the Stagehand browser tool to complete this task accurately and efficiently.
            """,
            agent=automation_agent,
            output_pydantic=AutomationResult,
            expected_output="""A structured result containing success status, extracted data, 
            any error messages, and a summary of actions performed.""",
        )

        crew = Crew(agents=[automation_agent], tasks=[automation_task], verbose=True)
        result = crew.kickoff()
        
        # FIX: Access the Pydantic model through .pydantic attribute
        automation_result = result.pydantic  # This gets the AutomationResult object
        
        return {
            "success": automation_result.success,
            "data": automation_result.data,
            "error_message": automation_result.error_message,
            "actions_performed": automation_result.actions_performed,
        }

    @listen(handle_browser_automation)
    def synthesize_result(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Create a user-friendly response from the automation results."""
        print("📝 Synthesizing final response...")

        synthesis_agent = Agent(
            role="Response Synthesis Specialist",
            goal="Transform technical automation results into clear, actionable user responses",
            backstory="""You are an expert communicator who specializes in translating 
            complex technical results into user-friendly responses. You excel at providing 
            clear summaries, actionable insights, and helpful recommendations.""",
            llm=response_llm,
        )

        synthesis_task = Task(
            description=f"""
            Create a comprehensive, user-friendly response based on the automation results:
            
            Automation Success: {inputs['success']}
            Data/Results: {inputs['data']}
            Error Message: {inputs.get('error_message', 'None')}
            Actions Performed: {inputs.get('actions_performed', 'Not specified')}
            
            Your response should include:
            1. A clear summary of what was accomplished
            2. Detailed results or findings
            3. Any relevant recommendations or next steps
            4. If there were errors, provide helpful guidance
            
            Make the response conversational, informative, and actionable for the end user.
            """,
            agent=synthesis_agent,
            output_pydantic=FinalResponse,
            expected_output="""A well-structured final response with summary, details, 
            and recommendations for the user.""",
        )

        crew = Crew(agents=[synthesis_agent], tasks=[synthesis_task], verbose=True)
        final_result = crew.kickoff()
        
        # FIX: Access the Pydantic model through .pydantic attribute
        response = final_result.pydantic  # This gets the FinalResponse object
        
        # Update the flow state
        self.state.result = f"""
        **Summary:** {response.summary}
        
        **Details:** {response.details}
        
        **Recommendations:** {response.recommendations or 'No additional recommendations at this time.'}
        """
        
        return {"result": self.state.result}


# Streamlit Frontend
def run_streamlit_app():
    st.set_page_config(page_title="Browser Automation Agent", page_icon="🤖")
    st.title("🤖 Browser Automation Agent")
    st.write(
        "Enter your browser automation query below. "
        "For example: `give the definition of pandas:https://pandas.pydata.org/`"
    )

    # User input
    user_query = st.text_input("Automation Query", value="", help="Describe your automation task and (optionally) include a URL.")

    if st.button("Run Automation") and user_query.strip():
        with st.spinner("Running browser automation..."):
            flow = BrowserAutomationFlow()
            flow.state.query = user_query.strip()

            # Run the flow asynchronously and display result
            try:
                result = asyncio.run(flow.kickoff_async())
            except RuntimeError as e:
                # For Streamlit, handle nested event loop (e.g., in Jupyter/Colab)
                if "asyncio.run() cannot be called from a running event loop" in str(e):
                    loop = asyncio.get_event_loop()
                    result = loop.run_until_complete(flow.kickoff_async())
                else:
                    raise

            st.success("Automation completed!")
            st.markdown(result["result"])
    else:
        st.info("Enter a query and click 'Run Automation' to get started.")

# Only run Streamlit frontend if this file is executed directly
if __name__ == "__main__":
    run_streamlit_app()
