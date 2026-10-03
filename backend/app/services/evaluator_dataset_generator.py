import json
import os
import random
from typing import List, Dict, Any

# Curated high-yield training calibration seeds across all 7 core domains
EVALUATION_CALIBRATION_SEEDS = [
    # --- DSA ---
    {
        "subject": "DSA",
        "topic": "Arrays & Two-Pointer",
        "difficulty": 2,
        "question": "Given an unsorted array of integers and a target sum, how would you determine if any two elements add up to the target?",
        "answers": [
            {
                "answer": "We can maintain a Hash Set or Hash Map while iterating through the array. For each number x, check if (target - x) is already in the set. If so, return true. Otherwise insert x. This takes O(n) time and O(n) space.",
                "score": 9.5,
                "sub_scores": {"technical_accuracy": 10.0, "clarity": 9.5, "completeness": 9.0, "depth": 9.5},
                "feedback": "Optimal O(n) hash-based approach with exact complement lookup. Stated both time and space complexity cleanly.",
                "improved": "Complement lookup via Hash Table achieves optimal O(n) time and O(n) space compared to O(n^2) brute-force."
            },
            {
                "answer": "We can sort the array first, which takes n log n, and then use two pointers from left and right. Move left up if sum is too small, move right down if sum is too big.",
                "score": 7.5,
                "sub_scores": {"technical_accuracy": 8.0, "clarity": 8.0, "completeness": 7.0, "depth": 7.0},
                "feedback": "Valid two-pointer technique correctly described, but did not mention that Hash Map can achieve O(n) time without sorting.",
                "improved": "Sorting with two pointers gives O(n log n) time and O(1) space, while a Hash Set achieves O(n) time with O(n) space."
            },
            {
                "answer": "Use two nested loops to check every pair in the array and see if they equal the target.",
                "score": 4.5,
                "sub_scores": {"technical_accuracy": 5.0, "clarity": 6.0, "completeness": 4.0, "depth": 3.0},
                "feedback": "Brute-force approach works but is inefficient at O(n^2). Senior interviews expect the O(n) hash map or O(n log n) two-pointer optimization.",
                "improved": "While brute force is O(n^2), hashing visited elements reduces lookup time to O(n) in a single pass."
            }
        ]
    },
    # --- Operating Systems ---
    {
        "subject": "OS",
        "topic": "Deadlocks & Synchronization",
        "difficulty": 3,
        "question": "What are the four necessary conditions for a deadlock to occur, and how does deadlock avoidance differ from deadlock prevention?",
        "answers": [
            {
                "answer": "The four Coffman conditions are Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait. Deadlock prevention statically invalidates at least one condition (e.g. strict resource ordering). Deadlock avoidance dynamically evaluates resource allocation states using Banker's Algorithm to guarantee the system stays in a safe state.",
                "score": 9.8,
                "sub_scores": {"technical_accuracy": 10.0, "clarity": 10.0, "completeness": 9.5, "depth": 9.5},
                "feedback": "Exemplary answer accurately listing all 4 Coffman conditions and distinguishing static prevention from dynamic avoidance via safe states.",
                "improved": "Deadlock prevention eliminates at least one of the 4 Coffman conditions by design, while avoidance dynamically tracks safe allocation states."
            },
            {
                "answer": "Deadlock needs mutual exclusion, hold and wait, and circular wait. Prevention means you stop deadlocks before they happen, and avoidance means you avoid them when programs run.",
                "score": 5.0,
                "sub_scores": {"technical_accuracy": 5.5, "clarity": 5.5, "completeness": 5.0, "depth": 4.0},
                "feedback": "Missed the 'No Preemption' condition. The explanation of prevention vs avoidance is colloquial and lacks mention of the Banker's Algorithm or safe states.",
                "improved": "Name all 4 conditions clearly and emphasize that avoidance uses algorithms like Banker's to dynamically test for safe execution sequences."
            },
            {
                "answer": "Deadlocks happen when processes get stuck waiting for each other. You just kill the process to fix it.",
                "score": 2.5,
                "sub_scores": {"technical_accuracy": 3.0, "clarity": 4.0, "completeness": 2.0, "depth": 1.0},
                "feedback": "Describes deadlock recovery (process termination) rather than prevention or avoidance. Failed to list the 4 necessary conditions.",
                "improved": "Focus on the four theoretical conditions and specify that prevention removes a condition while avoidance dynamically monitors safe states."
            }
        ]
    },
    # --- DBMS ---
    {
        "subject": "DBMS",
        "topic": "Indexing & Storage",
        "difficulty": 3,
        "question": "What is the structural and performance difference between a Clustered Index and a Non-Clustered Index?",
        "answers": [
            {
                "answer": "A Clustered Index dictates the physical ordering of records on disk; therefore, a table can only have one clustered index. Non-clustered indexes create a separate B-tree structure where leaf nodes contain pointers (or primary keys) to the actual data rows. Range scans on clustered keys are significantly faster because data pages are contiguous.",
                "score": 9.6,
                "sub_scores": {"technical_accuracy": 10.0, "clarity": 9.5, "completeness": 9.5, "depth": 9.5},
                "feedback": "Clear, precise explanation of physical storage order vs pointer-based secondary structures. Correctly noted the single clustered index constraint.",
                "improved": "Clustered indexes order data physically on disk (one per table), whereas non-clustered indexes are secondary B-trees containing row pointers."
            },
            {
                "answer": "Clustered index is on the primary key, and non-clustered is on other columns. Clustered is faster for searches.",
                "score": 5.5,
                "sub_scores": {"technical_accuracy": 6.0, "clarity": 6.5, "completeness": 5.0, "depth": 4.5},
                "feedback": "Partially accurate about primary keys, but misses the core technical principle: clustered index dictates physical disk page arrangement.",
                "improved": "Clarify that clustered indexes determine physical storage order, enabling efficient range scans, while non-clustered indexes require pointer indirection."
            }
        ]
    },
    # --- Computer Networks ---
    {
        "subject": "Computer Networks",
        "topic": "Transport Layer Protocols",
        "difficulty": 2,
        "question": "Explain the differences between TCP and UDP in terms of reliability, header overhead, and transmission mechanisms.",
        "answers": [
            {
                "answer": "TCP is a connection-oriented protocol that establishes a 3-way handshake (SYN, SYN-ACK, ACK), guarantees reliable delivery via acknowledgments, retransmissions, and flow/congestion control, but incurs a 20-byte minimum header. UDP is connectionless, sends datagrams without handshakes or delivery guarantees, and has an 8-byte header, making it ideal for low-latency streaming and gaming.",
                "score": 9.7,
                "sub_scores": {"technical_accuracy": 10.0, "clarity": 9.5, "completeness": 9.5, "depth": 9.5},
                "feedback": "Covers handshake, reliability mechanisms, byte overhead (20B vs 8B), and appropriate use cases thoroughly.",
                "improved": "TCP provides guaranteed, ordered byte-streams with flow control (20B header), whereas UDP is connectionless with low overhead (8B header)."
            },
            {
                "answer": "TCP is slow and safe, UDP is fast and loses packets.",
                "score": 4.0,
                "sub_scores": {"technical_accuracy": 5.0, "clarity": 5.0, "completeness": 3.0, "depth": 3.0},
                "feedback": "Too informal and simplistic. Needs to discuss connection establishment, headers, sequence numbers, and congestion control.",
                "improved": "State that TCP establishes connections and guarantees delivery through sequence numbers and acknowledgments, while UDP omits these for lower latency."
            }
        ]
    },
    # --- OOPs ---
    {
        "subject": "OOPs",
        "topic": "Polymorphism & Virtual Functions",
        "difficulty": 2,
        "question": "What is the difference between method overloading and method overriding, and how does runtime polymorphism work under the hood?",
        "answers": [
            {
                "answer": "Method overloading occurs at compile time within the same class when methods share a name but differ in parameter count or types. Method overriding occurs at runtime when a subclass redefines a virtual method of its parent with identical signature. Under the hood, runtime polymorphism uses a virtual method table (vtable) and vpointer to resolve the concrete implementation dynamically.",
                "score": 9.8,
                "sub_scores": {"technical_accuracy": 10.0, "clarity": 9.5, "completeness": 10.0, "depth": 9.5},
                "feedback": "Superb answer accurately contrasting static vs dynamic binding and articulating the vtable/vptr dispatch mechanism.",
                "improved": "Overloading is resolved at compile time by signature, whereas overriding uses vtables at runtime for dynamic method dispatch."
            },
            {
                "answer": "Overloading is same name different parameters. Overriding is changing code in child class.",
                "score": 6.0,
                "sub_scores": {"technical_accuracy": 7.0, "clarity": 6.5, "completeness": 5.5, "depth": 5.0},
                "feedback": "Correct basic definitions, but missed explaining compile-time vs runtime binding and how the virtual table resolves calls.",
                "improved": "Highlight that overloading is static polymorphism resolved by the compiler, while overriding relies on dynamic dispatch at runtime."
            }
        ]
    },
    # --- HR & Behavioral ---
    {
        "subject": "HR & Behavioral",
        "topic": "Conflict Resolution & STAR",
        "difficulty": 2,
        "question": "Tell me about a situation where you had a major disagreement with a team member. How did you resolve it?",
        "answers": [
            {
                "answer": "In our college capstone project, my teammate and I disagreed on whether to use SQL vs MongoDB. Using the STAR framework: Situation: We were building an inventory tracker with strict schema requirements. Task: Choose the database architecture without stalling the sprint. Action: I scheduled a short design review where we benchmarked our data access patterns against ACID requirements. Result: We agreed on PostgreSQL with JSONB support, meeting both structured and flexible needs, and delivered on time.",
                "score": 9.5,
                "sub_scores": {"technical_accuracy": 9.5, "clarity": 9.5, "completeness": 9.5, "depth": 9.5},
                "feedback": "Excellent use of the STAR format. Grounded the conflict in a realistic technical disagreement resolved through objective data and collaborative compromise.",
                "improved": "Structure with clear Situation, Task, Action (collaborative data-driven meeting), and positive measurable Result."
            },
            {
                "answer": "I argued with my friend about the code, so I just did the whole project myself so there were no more fights.",
                "score": 2.5,
                "sub_scores": {"technical_accuracy": 2.0, "clarity": 4.0, "completeness": 2.0, "depth": 2.0},
                "feedback": "Displays poor teamwork, failure to communicate, and lack of professional conflict resolution skills.",
                "improved": "Demonstrate active listening, finding common technical ground, and reaching a consensus rather than isolating oneself."
            }
        ]
    },
    # --- Aptitude ---
    {
        "subject": "Aptitude",
        "topic": "Time, Speed & Distance",
        "difficulty": 1,
        "question": "A train 150m long travels at 90 km/h. How much time does it take to cross a 300m bridge?",
        "answers": [
            {
                "answer": "Total distance to cover is train length plus bridge length: 150m + 300m = 450m. Convert speed from km/h to m/s: 90 * (5/18) = 25 m/s. Time = Distance / Speed = 450 / 25 = 18 seconds.",
                "score": 10.0,
                "sub_scores": {"technical_accuracy": 10.0, "clarity": 10.0, "completeness": 10.0, "depth": 10.0},
                "feedback": "Perfect step-by-step conversion, formulation, and calculation yielding 18 seconds.",
                "improved": "Total distance = 150 + 300 = 450m; Speed = 90 * (5/18) = 25 m/s; Time = 450 / 25 = 18 seconds."
            },
            {
                "answer": "It will take around 18 seconds because you add the distances and divide by the speed.",
                "score": 7.0,
                "sub_scores": {"technical_accuracy": 8.0, "clarity": 7.0, "completeness": 6.5, "depth": 6.5},
                "feedback": "Correct final answer, but omitted showing the 5/18 conversion from km/h to m/s explicitly.",
                "improved": "State the units conversion explicitly: 90 km/h = 25 m/s, then 450m / 25 m/s = 18 seconds."
            }
        ]
    }
]

def generate_lora_dataset(output_dir: str = "data/fine_tuning") -> Dict[str, int]:
    """
    Builds training and validation datasets formatted for instruction fine-tuning.
    Generates train.jsonl and val.jsonl in the output directory.
    """
    os.makedirs(output_dir, exist_ok=True)
    dataset = []

    for seed in EVALUATION_CALIBRATION_SEEDS:
        q_text = seed["question"]
        topic = seed["topic"]
        subject = seed["subject"]
        difficulty = seed["difficulty"]

        for item in seed["answers"]:
            instruction = (
                "You are an expert technical interview evaluator. Assess the candidate's answer to the technical interview question "
                "on a 0.0 to 10.0 scale with detailed sub-scores (technical_accuracy, clarity, completeness, depth), "
                "actionable feedback, and an improved sample answer. Respond strictly in JSON format."
            )
            input_text = (
                f"Subject: {subject}\n"
                f"Topic: {topic}\n"
                f"Difficulty: {difficulty}/5\n"
                f"Question: {q_text}\n"
                f"Candidate Answer: {item['answer']}"
            )
            output_json = {
                "score": item["score"],
                "sub_scores": item["sub_scores"],
                "feedback": item["feedback"],
                "improved_sample_answer": item["improved"]
            }

            dataset.append({
                "instruction": instruction,
                "input": input_text,
                "output": json.dumps(output_json)
            })

    # Shuffle and split 80% train / 20% validation
    random.seed(42)
    random.shuffle(dataset)
    split_idx = max(1, int(len(dataset) * 0.8))
    train_data = dataset[:split_idx]
    val_data = dataset[split_idx:]

    train_path = os.path.join(output_dir, "train.jsonl")
    val_path = os.path.join(output_dir, "val.jsonl")

    with open(train_path, "w", encoding="utf-8") as f:
        for row in train_data:
            f.write(json.dumps(row) + "\n")

    with open(val_path, "w", encoding="utf-8") as f:
        for row in val_data:
            f.write(json.dumps(row) + "\n")

    return {
        "total_examples": len(dataset),
        "train_examples": len(train_data),
        "val_examples": len(val_data),
        "train_file": train_path,
        "val_file": val_path
    }

if __name__ == "__main__":
    stats = generate_lora_dataset()
    print(f"Generated LoRA Fine-Tuning Dataset: {stats}")
