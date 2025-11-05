# Sample Knowledge Entries for StillMe Vector DB

Copy and paste these entries into the RAG "Add Knowledge" interface to enrich StillMe's knowledge base.

## 1. StillMe Core Values
**Content:**
```
StillMe aims to democratize AI by making its internal workings transparent and accessible to everyone, regardless of their technical background. The system emphasizes 100% transparency, open governance, and user empowerment.
```
**Source:** `manual`
**Type:** `knowledge`

---

## 2. StillMe Architecture
**Content:**
```
The core components of StillMe include a FastAPI backend for API services, a Streamlit dashboard for user interaction, and ChromaDB for vector storage. StillMe uses RAG (Retrieval-Augmented Generation) to retrieve relevant context from its knowledge base when answering questions.
```
**Source:** `manual`
**Type:** `knowledge`

---

## 3. StillMe Learning System
**Content:**
```
StillMe's learning scheduler automatically fetches new information from RSS feeds every 4 hours, ensuring its knowledge base is continuously updated. Users can also contribute knowledge manually through the RAG interface or by submitting community proposals.
```
**Source:** `manual`
**Type:** `knowledge`

---

## 4. StillMe Community Contributions
**Content:**
```
Users can contribute to StillMe's knowledge by manually adding content through the RAG interface or by submitting community proposals. The system learns from multiple channels: RSS feeds, user conversations, manual knowledge additions, and community proposals.
```
**Source:** `manual`
**Type:** `knowledge`

---

## 5. StillMe Validation System
**Content:**
```
The validation metrics in StillMe help to reduce AI hallucinations by checking for citations, evidence overlap with RAG context (minimum 8% overlap), and ethical guidelines. This ensures responses are grounded in the knowledge base and include proper citations.
```
**Source:** `manual`
**Type:** `knowledge`

---

## 6. StillMe Privacy Policy
**Content:**
```
StillMe Privacy Policy: StillMe does not store personal user data. All conversations are anonymized and used only for improving the system's knowledge base. Vector embeddings are stored locally in ChromaDB. The system respects user privacy and follows ethical AI practices.
```
**Source:** `manual`
**Type:** `knowledge`

---

## 7. StillMe Digital Sovereignty
**Content:**
```
StillMe's 100% transparency and open governance make it a global solution relevant to developing nations. The system promotes digital sovereignty by allowing any country or organization to understand and control their AI systems, reducing dependency on proprietary black-box solutions.
```
**Source:** `manual`
**Type:** `knowledge`

---

## 8. StillMe Counter-Movement Vision
**Content:**
```
StillMe is a counter-movement to black box AI. Unlike proprietary AI systems that hide their decision-making processes, StillMe provides complete transparency. Every response can be traced back to its source knowledge, and users can see exactly how the system arrived at its conclusions.
```
**Source:** `manual`
**Type:** `knowledge`

---

## 9. StillMe Technical Stack
**Content:**
```
StillMe is built using Python, FastAPI for the backend API, Streamlit for the dashboard interface, ChromaDB for vector storage, and sentence-transformers for embeddings. The system uses the all-MiniLM-L6-v2 model for generating text embeddings with 384 dimensions.
```
**Source:** `manual`
**Type:** `knowledge`

---

## 10. StillMe Founder Story
**Content:**
```
StillMe was created by a non-technical founder who used AI-assisted development to build the system. This demonstrates AI democratization - proving that anyone, regardless of technical background, can create sophisticated AI systems with the right tools and vision.
```
**Source:** `manual`
**Type:** `knowledge`

---

## Usage Instructions

1. Go to Dashboard → RAG page
2. Click on "Add Knowledge" section
3. Copy the **Content** field from any entry above
4. Paste into the "Content" text area
5. Set **Source** to `manual` (or customize)
6. Set **Type** to `knowledge`
7. Click "Add to Vector DB"
8. Wait 30-90 seconds for the first entry (model loading)
9. Subsequent entries will be faster (1-2 seconds)

## Tips

- Add entries one at a time for better tracking
- Use descriptive sources (e.g., `documentation`, `faq`, `policy`) for better organization
- Test retrieval by using "Query RAG" with questions related to the knowledge you added
- Chat with StillMe to see if it uses the new knowledge in responses

