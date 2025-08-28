
# user_id, password
users_test_data = [
    ("mike", "wazowski"),
    ("james", "sullivan")
]
"""
    user_id (user), password (user)
"""

projects_test_data = [
    ("Monster INC.", "Cool movie"),
    ("Cars", "Nice movie")
]
"""
    name (project), description (project)

"""

user_project_test_data = [
    (
        {
            "user_id": "mike", 
            "password": "wazowski", 
            "name": "Monster INC.", 
            "description": "Cool movie", 
            "permission": "owner"
        },
        {
            "user_id": "james", 
            "password": "sullivan", 
            "permission": "participant"
        }
    
    ),
    (
        {
            "user_id": "james", 
            "password": "sullivan", 
            "name": "Cars", 
            "description": "Nice movie", 
            "permission": "owner"
        },
        {
            "user_id": "mike", 
            "password": "wazowski", 
            "permission": "participant"
        }
    )
]
"""
    #### first dict: 
    - user_id (users), password (users), name (projects), description (users), expected (owner)
    
    #### second dict: 
    - user_id (users), password (users), expected (participant)
"""