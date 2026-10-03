# Subject PDFs Ingestion Directory

Drop your interview preparation and syllabus PDF documents into their respective subject folders below:

- `dsa/`: Data Structures & Algorithms notes, cheat-sheets, interview problem sets
- `os/`: Operating Systems lecture notes, process scheduling, memory management, deadlocks
- `dbms/`: Database Management Systems, SQL, normalization, transactions, concurrency
- `computer_networks/`: OSI/TCP-IP, protocols, routing, network security notes
- `oops/`: Object-Oriented Programming, design patterns, SOLID principles
- `hr_behavioral/`: HR interview question banks, STAR method guides, behavioral scenarios
- `aptitude/`: Quantitative aptitude, logical reasoning, verbal ability notes

### How It Works
When the PDF ingestion pipeline runs (Phase 1):
1. Text is extracted from each PDF in these folders.
2. The extracted text is split into semantic chunks (300-500 tokens with overlap).
3. Embeddings are generated for each chunk.
4. Chunks are stored in the `pdf_chunks` table in the database and queried dynamically during interview question generation (Blended RAG).
