import logging
from sqlalchemy.orm import Session
from backend.app.models.all_models import Subject, Topic, QuestionBank
from backend.app.services.embedding_service import _local_semantic_embedding, EMBEDDING_DIM

logger = logging.getLogger("uvicorn.error")

SUBJECT_TOPIC_DATA = [
    {
        "id": "dsa",
        "name": "Data Structures & Algorithms",
        "description": "Core algorithmic problems, data structures, complexity analysis, and coding implementations.",
        "topics": [
            {"id": "dsa_basic_math_logic", "name": "Basic Math, Number Theory & Series Logic", "range": "1-2"},
            {"id": "dsa_arrays_strings", "name": "Arrays and Strings", "range": "1-5"},
            {"id": "dsa_linked_lists", "name": "Linked Lists", "range": "1-4"},
            {"id": "dsa_stacks_queues", "name": "Stacks and Queues", "range": "1-4"},
            {"id": "dsa_trees", "name": "Binary Trees and BST", "range": "1-5"},
            {"id": "dsa_graphs", "name": "Graphs and Traversals", "range": "2-5"},
            {"id": "dsa_dp", "name": "Dynamic Programming", "range": "2-5"},
            {"id": "dsa_sorting_searching", "name": "Sorting and Searching", "range": "1-4"},
            {"id": "dsa_recursion", "name": "Recursion and Backtracking", "range": "2-5"},
            {"id": "dsa_complexity", "name": "Complexity Analysis & Big-O", "range": "1-3"},
        ]
    },
    {
        "id": "os",
        "name": "Operating Systems",
        "description": "Kernel architecture, process lifecycle, memory management, deadlocks, and virtualization.",
        "topics": [
            {"id": "os_process_threads", "name": "Process and Thread Management", "range": "1-4"},
            {"id": "os_cpu_scheduling", "name": "CPU Scheduling Algorithms", "range": "1-4"},
            {"id": "os_deadlocks", "name": "Deadlocks and Prevention", "range": "2-5"},
            {"id": "os_memory_paging", "name": "Memory Management and Paging", "range": "1-5"},
            {"id": "os_file_systems", "name": "File Systems and Storage (RAID)", "range": "1-4"},
            {"id": "os_synchronization", "name": "Process Synchronization and Semaphores", "range": "2-5"},
        ]
    },
    {
        "id": "dbms",
        "name": "DBMS & SQL",
        "description": "Relational schemas, SQL queries, indexing strategies, normalization, transactions, and ACID.",
        "topics": [
            {"id": "dbms_normalization", "name": "Normalization (1NF to BCNF)", "range": "1-4"},
            {"id": "dbms_sql_queries", "name": "SQL Queries, Aggregations, and Subqueries", "range": "1-5"},
            {"id": "dbms_transactions_acid", "name": "Transactions and ACID Properties", "range": "1-5"},
            {"id": "dbms_indexing", "name": "Indexing (B-Tree, Hash, Clustered)", "range": "2-5"},
            {"id": "dbms_joins", "name": "Joins and Query Optimization", "range": "1-4"},
            {"id": "dbms_concurrency", "name": "Concurrency Control and MVCC", "range": "2-5"},
            {"id": "dbms_distributed", "name": "Sharding, Partitioning, and CAP Theorem", "range": "3-5"},
        ]
    },
    {
        "id": "computer_networks",
        "name": "Computer Networks",
        "description": "Network protocols, OSI/TCP-IP models, packet routing, DNS, security, and sockets.",
        "topics": [
            {"id": "cn_osi_tcp", "name": "OSI and TCP/IP Layer Models", "range": "1-4"},
            {"id": "cn_routing", "name": "Routing, Switching, and Devices", "range": "1-4"},
            {"id": "cn_dns_http", "name": "DNS, HTTP, HTTPS, and Web Protocols", "range": "1-4"},
            {"id": "cn_sockets_transport", "name": "TCP vs UDP and Transport Layer", "range": "1-5"},
            {"id": "cn_dhcp_ip", "name": "IP Addressing, Subnetting, and DHCP", "range": "1-4"},
            {"id": "cn_security", "name": "Network Security, Firewalls, and VPNs", "range": "2-5"},
        ]
    },
    {
        "id": "oops",
        "name": "Object-Oriented Programming",
        "description": "Class design, 4 pillars, polymorphism, inheritance, exception handling, and design patterns.",
        "topics": [
            {"id": "oops_pillars", "name": "Four Pillars (Encapsulation, Abstraction, Inheritance, Polymorphism)", "range": "1-4"},
            {"id": "oops_polymorphism", "name": "Overloading, Overriding, and Virtual Functions", "range": "1-5"},
            {"id": "oops_solid", "name": "SOLID Principles", "range": "2-5"},
            {"id": "oops_design_patterns", "name": "Design Patterns (Singleton, Factory, Observer)", "range": "2-5"},
            {"id": "oops_memory_exceptions", "name": "Constructors, Destructors, GC, and Exceptions", "range": "1-4"},
        ]
    },
    {
        "id": "hr_behavioral",
        "name": "HR & Behavioral",
        "description": "Situational questions, leadership, team conflict, STAR framework, and motivation.",
        "topics": [
            {"id": "hr_intro_vision", "name": "Introduction, Strengths, Weaknesses, and Career Goals", "range": "1-3"},
            {"id": "hr_star", "name": "STAR Method Scenarios (Challenge, Leadership, Failure)", "range": "1-4"},
            {"id": "hr_conflict", "name": "Conflict Resolution and Teamwork", "range": "1-4"},
            {"id": "hr_company_culture", "name": "Company Knowledge, Work Ethics, and Adaptability", "range": "1-3"},
        ]
    },
    {
        "id": "aptitude",
        "name": "Quantitative & Logical Aptitude",
        "description": "Math, series, verbal reasoning, logical puzzles, and fundamental technical screening.",
        "topics": [
            {"id": "apt_quant", "name": "Quantitative Aptitude (Speed, Distance, Work, Interest)", "range": "1-4"},
            {"id": "apt_logical", "name": "Logical Reasoning, Codes, and Series", "range": "1-4"},
            {"id": "apt_verbal", "name": "Verbal Ability, Antonyms, and Synonyms", "range": "1-3"},
            {"id": "apt_tech_screen", "name": "Core CS Technical Screening Concepts", "range": "1-3"},
        ]
    }
]

# Seed Questions for Question Bank bootstrap
SEED_QUESTION_BANK = [
    # Foundational Math, Number Theory & Series Logic (Levels 1 - 2)
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Check whether a given integer N is prime in optimal O(sqrt(N)) time. Explain why checking up to sqrt(N) is sufficient."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 2, "question_type": "coding", "source": "seed",
     "question_text": "Print all prime numbers from 1 to N using the Sieve of Eratosthenes. Compare its time complexity with trial division."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Write a function to compute the factorial of a number N both iteratively and recursively. Explain the call stack space overhead."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Generate the Fibonacci series up to N terms. How can you optimize the solution to O(1) auxiliary space?"},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Write a function to print all Fibonacci numbers strictly less than a given integer N."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Reverse a given integer N without converting it to a string, using modulo (%) and integer division (//). Handle negative integers."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Check whether a number is a palindrome without converting it to a string. Walk through your digit reversal approach."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Check whether an integer N is an Armstrong (Narcissistic) number, where the sum of each digit raised to the power of the number of digits equals N."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Write a function to calculate both the sum of digits and the product of digits of a given positive integer N in O(log10 N) time."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Count the number of digits in an integer N using both a loop-based extraction and a mathematical log10 formula."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Check whether a number is even or odd without using the modulo (%) operator. Explain how bitwise AND (N & 1) accomplishes this."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Find the Greatest Common Divisor (GCD/HCF) of two integers using the Euclidean algorithm. What is its logarithmic time complexity?"},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Calculate the Least Common Multiple (LCM) of two numbers using their GCD and the mathematical property a * b = gcd(a, b) * lcm(a, b)."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Find all factors/divisors of a number N in O(sqrt(N)) time. Return the count of factors and their sum."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Check whether a number is a Perfect Number (equal to the sum of its proper positive divisors excluding itself, e.g. 6 = 1 + 2 + 3)."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Check whether a number is a Strong Number, where the sum of factorials of digits equals the original number (e.g., 145 = 1! + 4! + 5!)."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Check whether a number is an Automorphic Number (a number whose square ends in the same digits as the number itself, e.g., 25^2 = 625)."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Check whether a number is a Harshad (Niven) number, meaning it is divisible by the sum of its digits (e.g., 18 is divisible by 1 + 8 = 9)."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Find the largest digit and the smallest digit in a given number, and count the frequency of a specified target digit."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 2, "question_type": "coding", "source": "seed",
     "question_text": "Implement pow(x, n) to calculate x raised to power n without using built-in pow() in O(log n) time using binary exponentiation."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Swap two numbers without using a third temporary variable. Demonstrate both the arithmetic (+, -) and bitwise XOR (^) methods."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Find the largest and smallest of three numbers using minimal conditional branch checks."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Write a function to compute the sum of series 1 + 2 + ... + N. Compare the O(N) iterative loop with Gauss's O(1) formula N*(N+1)/2."},
    {"topic_id": "dsa_basic_math_logic", "difficulty": 1, "question_type": "coding", "source": "seed",
     "question_text": "Print the multiplication table of a number N from 1 to 10 in a clean, aligned format."},

    # DSA
    {"topic_id": "dsa_arrays_strings", "difficulty": 2, "question_type": "coding", "source": "seed",
     "question_text": "Given an array of integers nums and an integer target, write a function to return indices of the two numbers such that they add up to target. What is the time and space complexity?"},
    {"topic_id": "dsa_arrays_strings", "difficulty": 1, "question_type": "conceptual", "source": "seed",
     "question_text": "Explain Kadane's algorithm for finding the maximum contiguous subarray sum. What is its time complexity compared to a brute-force approach?"},
    {"topic_id": "dsa_linked_lists", "difficulty": 2, "question_type": "coding", "source": "seed",
     "question_text": "Write a function to detect whether a cycle exists in a singly linked list. Explain Floyd's Tortoise and Hare algorithm."},
    {"topic_id": "dsa_trees", "difficulty": 3, "question_type": "conceptual", "source": "seed",
     "question_text": "What is the difference between a Binary Search Tree (BST) and an AVL tree? How does tree rotation keep lookup operations O(log n)?"},
    {"topic_id": "dsa_dp", "difficulty": 3, "question_type": "coding", "source": "seed",
     "question_text": "Given an amount and an array of coin denominations, write an optimal function to find the minimum number of coins needed to make up that amount."},

    # OS
    {"topic_id": "os_deadlocks", "difficulty": 3, "question_type": "conceptual", "source": "seed",
     "question_text": "What are the four Coffman conditions necessary for a deadlock to occur? How does the Banker's algorithm achieve deadlock avoidance?"},
    {"topic_id": "os_memory_paging", "difficulty": 2, "question_type": "conceptual", "source": "seed",
     "question_text": "Explain the concept of Virtual Memory and Demand Paging. What is a page fault, and what steps does the OS take when it happens?"},
    {"topic_id": "os_cpu_scheduling", "difficulty": 2, "question_type": "conceptual", "source": "seed",
     "question_text": "Compare Round Robin scheduling with Shortest Remaining Time First (SRTF). In what scenario can SRTF lead to starvation?"},

    # DBMS
    {"topic_id": "dbms_indexing", "difficulty": 3, "question_type": "conceptual", "source": "seed",
     "question_text": "What is the physical and structural difference between a Clustered Index and a Non-Clustered Index in an RDBMS?"},
    {"topic_id": "dbms_normalization", "difficulty": 2, "question_type": "conceptual", "source": "seed",
     "question_text": "Explain 3NF versus BCNF with a concrete example. Why might a schema satisfy 3NF but still suffer from update anomalies?"},
    {"topic_id": "dbms_sql_queries", "difficulty": 2, "question_type": "coding", "source": "seed",
     "question_text": "Write an SQL query to retrieve the second highest salary from an Employee table without using the LIMIT keyword."},

    # Computer Networks
    {"topic_id": "cn_sockets_transport", "difficulty": 2, "question_type": "conceptual", "source": "seed",
     "question_text": "Walk me through the TCP 3-way handshake process. Why is UDP preferred over TCP for live video conferencing and gaming?"},
    {"topic_id": "cn_dns_http", "difficulty": 2, "question_type": "conceptual", "source": "seed",
     "question_text": "Describe the complete step-by-step resolution process that occurs when a user types 'https://google.com' into a browser until the page renders."},

    # OOPs
    {"topic_id": "oops_polymorphism", "difficulty": 2, "question_type": "conceptual", "source": "seed",
     "question_text": "Differentiate between compile-time method overloading and runtime method overriding. How does the virtual method table (vtable) enable dynamic dispatch?"},
    {"topic_id": "oops_pillars", "difficulty": 2, "question_type": "coding", "source": "seed",
     "question_text": "Design an abstract Vehicle class with encapsulated properties and write two subclasses (Car, Motorcycle) overriding a startEngine() method in Python or Java."},

    # HR & Behavioral
    {"topic_id": "hr_star", "difficulty": 1, "question_type": "conceptual", "source": "seed",
     "question_text": "Tell me about a time when you encountered a major technical roadblock or tight deadline in a project. How did you structure your solution using the STAR framework?"},

    # Aptitude
    {"topic_id": "apt_quant", "difficulty": 1, "question_type": "conceptual", "source": "seed",
     "question_text": "A train 150 meters long is traveling at 90 km/h. How many seconds will it take to cross a bridge 300 meters in length? Walk me through your mental calculation."}
]

def seed_database(db: Session):
    """
    Seeds subjects, topics, and initial calibrated question bank into the database.
    """
    # 1. Seed Subjects & Topics
    for sub_data in SUBJECT_TOPIC_DATA:
        subject = db.query(Subject).filter(Subject.id == sub_data["id"]).first()
        if not subject:
            subject = Subject(
                id=sub_data["id"],
                name=sub_data["name"],
                description=sub_data["description"]
            )
            db.add(subject)
            db.commit()

        for top_data in sub_data["topics"]:
            topic = db.query(Topic).filter(Topic.id == top_data["id"]).first()
            if not topic:
                topic = Topic(
                    id=top_data["id"],
                    subject_id=sub_data["id"],
                    name=top_data["name"],
                    difficulty_range=top_data["range"]
                )
                db.add(topic)
        db.commit()

    # 2. Seed Initial Question Bank
    for q_data in SEED_QUESTION_BANK:
        existing = db.query(QuestionBank).filter(QuestionBank.question_text == q_data["question_text"]).first()
        if not existing:
            emb = _local_semantic_embedding(q_data["question_text"], EMBEDDING_DIM)
            qb = QuestionBank(
                topic_id=q_data["topic_id"],
                difficulty=q_data["difficulty"],
                question_type=q_data["question_type"],
                question_text=q_data["question_text"],
                source=q_data["source"],
                embedding=emb
            )
            db.add(qb)
    db.commit()
    logger.info("Database seeding completed successfully.")
