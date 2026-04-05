# Plan: Rename System to KindGuard

The goal is to rename the security prototype from "MelodyWings" to **KindGuard** (a name more suited to the nonprofit's mission for neurodivergent and special needs children) and update the problem statement in the documentation.

## Proposed Changes

### Core Application
- **[MODIFY] [app.py](file:///c:/Users/atsha/Downloads/melodywings/app.py)**: Update window titles, headers, and dashboard labels from "MelodyWings" to **KindGuard**.
- **[MODIFY] [chat_analyzer.py](file:///c:/Users/atsha/Downloads/melodywings/chat_analyzer.py)**: Update simulator banners and comments.
- **[MODIFY] [reporting_utils.py](file:///c:/Users/atsha/Downloads/melodywings/reporting_utils.py)**: Update PDF report headers.

### Documentation
- **[MODIFY] [README.md](file:///c:/Users/atsha/Downloads/melodywings/README.md)**: 
    - Full rename to **KindGuard**.
    - Replace current description with the new problem statement: *"KindGuard is a nonprofit platform designed to support neurodivergent children and children with special needs by connecting them with volunteer mentors for personalized, interest-based learning."*
- **[MODIFY] [db_plan.md](file:///c:/Users/atsha/Downloads/melodywings/db_plan.md)**: Update internal planning titles.
- **[MODIFY] [part1_workflow.md](file:///c:/Users/atsha/Downloads/melodywings/part1_workflow.md)**: Update architecture overview titles.
- **[MODIFY] [part2_workflow.md](file:///c:/Users/atsha/Downloads/melodywings/part2_workflow.md)**: Update vision pipeline titles.

## Verification Plan

### Manual Verification
1. Run `streamlit run app.py` and verify all visual labels display **KindGuard**.
2. Run `python chat_analyzer.py` and check the CLI output name.
3. Generate a sample PDF report and verify the header.
4. Review **README.md** for the updated problem statement.
