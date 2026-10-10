"""Shared sample data for tests: one assessment, its rubric and a sample submission (s_1)."""

SAMPLE_SUBMISSION = (
    "# Collisions in hash tables\n\n"
    "A hash table stores key and value pairs in an array. A hash function turns each key "
    "into an index. Sometimes a collision happens when two keys map to the same index, "
    "and the table must still keep both values.\n\n"
    "There are two common ways to handle this. In chaining, each slot of the table holds "
    "a linked list of all the entries that landed there. A lookup hashes the key, then "
    "walks the short list in that slot. Open addressing instead probes for the next free "
    "slot in the array itself, for example by checking the next index (linear probing). "
    "Both methods keep every value but they behave differently when the table gets "
    "crowded.\n\n"
    "For time cost, lookups are fast, usually O(1) on average when the hash function "
    "spreads keys evenly. In the worst case all keys land in one slot and a lookup becomes "
    "O(n) for both methods. The load factor, the number of entries divided by the number "
    "of slots, tells us when to resize the table so that chains and probe sequences stay "
    "short.\n\n"
    "In short, collisions cannot be avoided, so a good table needs a good hash function, "
    "a collision strategy and a resize rule.\n"
)

RUBRIC = {
    "criteria": [
        {
            "id": "c1",
            "name": "Concept accuracy",
            "description": "Explains what a collision is and why it happens, correctly.",
            "max_marks": 5,
            "topic": "hashing",
            "levels": [
                "Absent or wrong",
                "Mentions the idea, mostly inaccurate",
                "Partly correct with clear gaps",
                "Mostly correct, minor gaps",
                "Correct, complete and precise",
            ],
        },
        {
            "id": "c2",
            "name": "Resolution strategies",
            "description": "Describes chaining and open addressing.",
            "max_marks": 5,
            "topic": "collisions",
            "levels": [
                "Absent or wrong",
                "Mentions one strategy vaguely",
                "Describes one well, or both vaguely",
                "Describes both mostly correctly",
                "Describes both accurately and clearly",
            ],
        },
        {
            "id": "c3",
            "name": "Complexity analysis",
            "description": "Analyzes time complexity correctly.",
            "max_marks": 5,
            "topic": "complexity",
            "levels": [
                "Absent or wrong",
                "Mentions O(1) without context",
                "Partly explains average vs worst case",
                "Good explanation with minor gaps",
                "Clear distinction between average and worst case",
            ],
        },
        {
            "id": "c4",
            "name": "Communication",
            "description": "Writing is clear and structured.",
            "max_marks": 5,
            "topic": "communication",
            "levels": [
                "Unreadable",
                "Hard to follow",
                "Readable but poorly structured",
                "Clear and mostly well structured",
                "Excellent structure and clarity",
            ],
        },
    ]
}
