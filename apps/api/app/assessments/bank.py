"""Built-in practice questions. They are used ONLY to top up an assessment when the AI service is slow, rate limited or not configured,
so that practice is never blocked. They are written for general role preparation (not tailored to a resume) and, like every question
here, they are practice questions and NEVER questions asked by a company."""

import random

from app.assessments import validate
from app.assessments.schemas import GenQuestion


def _mcq(topic: str, skills: list[str], diff: str, prompt: str, options: list[str], correct: int, why: str) -> dict:
    return {"type": "mcq", "topic": topic, "skills": skills, "difficulty": diff, "prompt": prompt, "options": options, "correct_index": correct, "explanation": why, "reference_points": []}


def _short(topic: str, skills: list[str], diff: str, prompt: str, points: list[str], why: str) -> dict:
    return {"type": "short_answer", "topic": topic, "skills": skills, "difficulty": diff, "prompt": prompt, "options": [], "correct_index": None, "explanation": why, "reference_points": points}


BANK: dict[str, list[dict]] = {
    "python": [
        _mcq("Python basics", ["python"], "easy", "What does the expression [x * 2 for x in range(3)] evaluate to in Python?", ["[2, 4, 6]", "[0, 2, 4]", "[0, 1, 2]", "[0, 2, 4, 6]"], 1, "range(3) yields 0, 1, 2, and each value is doubled."),
        _mcq("Python functions", ["python"], "medium", "Given def f(x, acc=[]): acc.append(x); return acc, what do the two separate statements print(f(1)) and then print(f(2)) output?", ["[1] then [2]", "[1] then [1, 2]", "[1, 2] then [1, 2]", "It raises an error"], 1, "The default list is created once and shared, so both calls return the same list object holding 1 and 2."),
        _mcq("Python data types", ["python"], "easy", "Which statement about Python tuples and lists is correct?", ["Tuples are mutable and lists are not", "Lists are mutable and tuples are not", "Both are immutable", "Tuples can only hold numbers"], 1, "Lists can be changed in place; tuples cannot."),
        _mcq("Python operators", ["python"], "medium", "What is the difference between == and is in Python?", ["They are identical", "== compares values, is compares object identity", "is compares values, == compares identity", "is only works with strings"], 1, "== checks equality of values; is checks whether two names refer to the same object."),
        _mcq("Python performance", ["python", "data structures"], "easy", "What is the average time complexity of looking up a key in a Python dictionary?", ["O(1)", "O(n)", "O(log n)", "O(n log n)"], 0, "Dictionaries are hash tables, so lookups are constant time on average."),
        _mcq("Python decorators", ["python"], "medium", "What does a Python decorator do?", ["Compiles a function to machine code", "Wraps a function to add behaviour without changing its code", "Declares a variable as constant", "Makes a function run in a new thread"], 1, "A decorator takes a function and returns a wrapped version of it."),
        _mcq("Python generators", ["python"], "medium", "What does the yield keyword do inside a function?", ["Ends the program", "Turns the function into a generator that produces values lazily", "Imports a module", "Raises an exception"], 1, "yield makes the function a generator that hands back one value at a time."),
        _mcq("Python context managers", ["python"], "medium", "Why is a with statement used when opening a file?", ["It makes reading faster", "It guarantees the file is closed even if an error occurs", "It encrypts the file", "It locks the file for other programs"], 1, "The context manager closes the file automatically when the block ends."),
        _mcq("Python concurrency", ["python"], "hard", "Which statement about the CPython Global Interpreter Lock (GIL) is correct?", ["It lets many threads run Python bytecode at the same time", "Only one thread executes Python bytecode at a time", "It only affects network code", "It was removed from all Python versions long ago"], 1, "The GIL allows one thread at a time to run Python bytecode, so CPU-bound threads do not run in parallel."),
        _mcq("Python functions", ["python"], "easy", "In def f(*args, **kwargs), what are kwargs?", ["A tuple of positional arguments", "A dictionary of extra keyword arguments", "A list of return values", "A reserved global variable"], 1, "**kwargs collects extra keyword arguments into a dictionary."),
        _mcq("Python errors", ["python"], "easy", "Which block always runs, whether or not an exception was raised?", ["try", "except", "finally", "else"], 2, "finally runs in every case, which makes it suitable for cleanup."),
        _mcq("Python objects", ["python"], "hard", "After b = copy.copy(a) where a = [[1], [2]], what happens if you run b[0].append(9)?", ["Only b changes", "The change is visible through a as well, because the inner lists are shared", "An error is raised", "Neither changes"], 1, "A shallow copy copies the outer list only; the inner lists are the same objects."),
        _short("Python generators", ["python"], "medium", "Explain the difference between a list and a generator, and give one situation where you would choose a generator.", ["A list stores all items in memory; a generator produces items one at a time", "Generators save memory on large or infinite sequences", "Generators can be iterated only once"], "A good answer contrasts memory use and laziness."),
        _short("Python tooling", ["python"], "easy", "What is a virtual environment in Python and why do developers use one for each project?", ["Isolated set of installed packages per project", "Avoids version conflicts between projects", "Makes dependencies reproducible (requirements file)"], "Isolation and reproducibility are the key points."),
        _short("APIs in Python", ["python", "rest api"], "medium", "Describe how you would design and validate a simple REST endpoint that creates a user in a Python web framework such as FastAPI or Flask.", ["Define the route and HTTP method (POST)", "Validate input with a schema or model", "Return proper status codes (201, 422/400)", "Handle errors and avoid leaking internals"], "Look for validation, status codes and error handling."),
    ],
    "ml": [
        _mcq("Overfitting", ["machine learning"], "easy", "What does it mean when a model is overfitting?", ["It performs poorly on training data", "It performs very well on training data but poorly on unseen data", "It trains too quickly", "It uses too little memory"], 1, "Overfitting means the model memorises training noise and does not generalise."),
        _mcq("Model evaluation", ["machine learning"], "easy", "What is the main purpose of holding out a test set?", ["To make training faster", "To estimate performance on unseen data once model choices are finished", "To increase the amount of training data", "To tune hyperparameters repeatedly"], 1, "The test set gives an unbiased estimate when it is used only at the end."),
        _mcq("Classification metrics", ["machine learning", "statistics"], "easy", "A spam filter flags 10 emails and 8 of them are really spam. What is its precision?", ["0.2", "0.5", "0.8", "1.0"], 2, "Precision is true positives divided by all predicted positives: 8 / 10 = 0.8."),
        _mcq("Class imbalance", ["machine learning"], "medium", "In a dataset where 99% of cases are negative, why can accuracy be misleading?", ["Accuracy cannot be computed", "A model that always predicts negative scores 99% while finding no positives", "Accuracy ignores the negative class", "Accuracy is always 50%"], 1, "High accuracy can hide a model that never detects the rare class."),
        _mcq("Optimisation", ["machine learning", "deep learning"], "medium", "What can happen if the learning rate in gradient descent is set far too large?", ["Training always becomes faster and better", "The loss may oscillate or diverge instead of converging", "The model becomes simpler", "Nothing, the learning rate is irrelevant"], 1, "Large steps can overshoot the minimum repeatedly."),
        _mcq("Regularisation", ["machine learning"], "medium", "What does L2 regularisation do?", ["Removes all features", "Penalises large weights to discourage overly complex models", "Doubles the training set", "Normalises the labels"], 1, "L2 adds a penalty on squared weights, which shrinks them."),
        _mcq("Bias and variance", ["machine learning"], "medium", "A model with very high variance typically shows:", ["High training error and high validation error", "Low training error but much higher validation error", "Identical training and validation error", "No error at all"], 1, "High variance means it fits the training data closely but generalises badly."),
        _mcq("Cross-validation", ["machine learning"], "easy", "What does k-fold cross-validation mainly help with?", ["Reducing dataset size", "Estimating generalisation performance more reliably using several train/validation splits", "Removing outliers", "Speeding up inference"], 1, "Averaging over folds gives a more stable performance estimate."),
        _mcq("Neural networks", ["deep learning"], "easy", "What does the ReLU activation function compute?", ["max(0, x)", "1 / (1 + e^-x)", "x squared", "The average of x"], 0, "ReLU returns x for positive inputs and 0 otherwise."),
        _mcq("Preprocessing", ["machine learning"], "medium", "Which algorithm is most sensitive to the scale of input features?", ["k-nearest neighbours", "Decision tree", "Random forest", "Gradient-boosted trees"], 0, "Distance-based methods like k-NN are affected by feature scale; tree models are not."),
        _mcq("Data leakage", ["machine learning"], "hard", "Which is an example of data leakage?", ["Splitting data before preprocessing", "Fitting a scaler on the whole dataset before the train/test split", "Using a validation set", "Shuffling the training data"], 1, "Information from the test rows leaks into training when the scaler sees them."),
        _mcq("Neural networks", ["deep learning"], "medium", "What does the softmax function output?", ["A single class label", "Probabilities that are non-negative and sum to 1", "The loss value", "Raw unbounded scores"], 1, "Softmax converts scores into a probability distribution over classes."),
        _short("Bias and variance", ["machine learning"], "medium", "Explain the bias-variance trade-off and how you would tell which one is hurting your model.", ["High bias = underfitting, high variance = overfitting", "Compare training and validation error", "Remedies: more data/regularisation for variance, more capacity/features for bias"], "Look for the diagnosis using training versus validation error."),
        _short("Class imbalance", ["machine learning"], "medium", "Describe two ways to handle a heavily imbalanced classification dataset.", ["Resampling (oversample minority / undersample majority)", "Class weights in the loss", "Use metrics such as precision, recall, F1 or PR-AUC"], "Any two valid techniques plus a suitable metric."),
        _short("LLM applications", ["rag", "llm"], "medium", "Explain how retrieval-augmented generation (RAG) works and one benefit over prompting a language model alone.", ["Retrieve relevant documents (embeddings, vector search)", "Add them to the prompt as context", "Benefit: fresher, grounded answers and fewer hallucinations"], "Retrieval plus grounding are the key ideas."),
    ],
    "data": [
        _mcq("SQL basics", ["sql"], "easy", "What is the difference between WHERE and HAVING in SQL?", ["They are identical", "WHERE filters rows before grouping; HAVING filters groups after aggregation", "HAVING filters rows before grouping", "WHERE only works with numbers"], 1, "HAVING is applied to aggregated groups."),
        _mcq("SQL joins", ["sql"], "easy", "What does a LEFT JOIN return?", ["Only rows that match in both tables", "All rows from the left table, with NULLs where the right table has no match", "All rows from the right table only", "The cross product of both tables"], 1, "Unmatched left rows are kept with NULLs for the right columns."),
        _mcq("pandas", ["pandas"], "easy", "What does df.groupby('a')['b'].mean() return?", ["The overall mean of column b", "The mean of b for each distinct value of a", "The mean of column a", "A copy of the DataFrame"], 1, "It groups rows by a and averages b inside each group."),
        _mcq("Statistics", ["statistics"], "easy", "Which measure is least affected by extreme outliers?", ["Mean", "Median", "Range", "Variance"], 1, "The median depends on the middle value, not on the extremes."),
        _mcq("Hypothesis testing", ["statistics"], "hard", "A p-value of 0.03 means:", ["There is a 97% chance the alternative hypothesis is true", "If the null hypothesis were true, results at least this extreme would occur about 3% of the time", "The effect size is 3%", "The null hypothesis is 3% likely"], 1, "A p-value is a probability about the data under the null, not about the hypotheses."),
        _mcq("Statistics", ["statistics"], "medium", "Ice cream sales and drowning incidents are strongly correlated. What is the most reasonable explanation?", ["Ice cream causes drowning", "Both rise in hot weather, a common cause", "Drowning causes ice cream sales", "The correlation must be a data error"], 1, "Correlation does not imply causation; a third factor (temperature) drives both."),
        _mcq("Statistics", ["statistics"], "easy", "In a normal distribution, about what share of values lie within one standard deviation of the mean?", ["50%", "68%", "95%", "99.7%"], 1, "The 68-95-99.7 rule: about 68% within one standard deviation."),
        _mcq("A/B testing", ["a/b testing", "statistics"], "medium", "Why are users randomly assigned to groups A and B in an experiment?", ["To make the test cheaper", "To make the groups comparable so differences can be attributed to the change", "To ensure group A is larger", "To hide the experiment from analysts"], 1, "Randomisation balances other factors across groups."),
        _mcq("Data visualisation", ["data visualization"], "easy", "Which chart is best for showing the distribution of one numeric variable?", ["Pie chart", "Histogram", "Line chart of unrelated points", "Treemap"], 1, "A histogram shows how values are spread across bins."),
        _mcq("SQL basics", ["sql"], "easy", "Which SQL keyword removes duplicate rows from a query result?", ["UNIQUE", "DISTINCT", "REMOVE", "SINGLE"], 1, "SELECT DISTINCT returns only unique rows."),
        _short("Analytics thinking", ["statistics", "sql"], "medium", "A key business metric dropped 20% overnight. How would you investigate whether it is a real change or a data problem?", ["Check data pipeline / tracking changes first", "Segment by time, platform, region, product", "Compare with other related metrics and look for recent releases or events"], "Look for a structured approach starting with data quality."),
        _short("Data cleaning", ["pandas"], "medium", "Describe how you would handle a column in which 30% of the values are missing before training a model.", ["Understand why it is missing (random or not)", "Options: drop, impute (mean/median/model), add a missing indicator", "Avoid leakage: fit imputers on training data only"], "Reasoning about the cause and avoiding leakage matter most."),
    ],
    "web": [
        _mcq("HTTP", ["rest api"], "easy", "What does the HTTP status code 404 mean?", ["The server crashed", "The requested resource was not found", "The request was successful", "Authentication is required"], 1, "404 Not Found means the server has no resource at that URL."),
        _mcq("JavaScript", ["javascript"], "easy", "What is the main difference between let and var in JavaScript?", ["let is block-scoped, var is function-scoped", "var is block-scoped, let is function-scoped", "They behave identically", "let cannot be reassigned"], 0, "let respects block scope; var is scoped to the function."),
        _mcq("JavaScript", ["javascript"], "easy", "What does === do in JavaScript?", ["Compares values only, converting types", "Compares value and type without coercion", "Assigns a value", "Compares object memory addresses only"], 1, "Strict equality does not convert types."),
        _mcq("CSS", ["css"], "easy", "In the CSS box model, which order lists the layers from the inside out?", ["Margin, border, padding, content", "Content, padding, border, margin", "Content, margin, padding, border", "Padding, content, margin, border"], 1, "An element's content is surrounded by padding, then border, then margin."),
        _mcq("Async JavaScript", ["javascript"], "medium", "What does await do inside an async function?", ["Blocks the whole browser", "Pauses that function until the promise settles, without blocking the main thread", "Creates a new thread", "Cancels the promise"], 1, "await suspends the async function while other code can keep running."),
        _mcq("React", ["react"], "medium", "Why does React ask for a key prop on items rendered from a list?", ["For styling", "To help React identify which items changed, were added or removed", "To sort the list", "To make items clickable"], 1, "Stable keys let React update only what changed."),
        _mcq("React", ["react"], "easy", "What happens when you call the setter returned by useState?", ["The page reloads", "React schedules a re-render with the new state", "The component is deleted", "Nothing until the next request"], 1, "State updates trigger a re-render of the component."),
        _mcq("REST", ["rest api"], "medium", "Which HTTP method is defined as idempotent for replacing a resource?", ["POST", "PUT", "PATCH always", "CONNECT"], 1, "Repeating the same PUT request leaves the resource in the same state."),
        _mcq("Web security", ["rest api"], "medium", "What does CORS control?", ["Database access", "Which other origins a browser may allow to read a server's responses", "Password hashing", "Image compression"], 1, "CORS is a browser mechanism relaxing the same-origin policy under server control."),
        _mcq("Web storage", ["javascript"], "medium", "How do cookies differ from localStorage?", ["Cookies are sent automatically to the server with matching requests; localStorage is not", "localStorage is sent with every request", "Cookies are never stored", "They are the same thing"], 0, "Only cookies are attached to requests automatically."),
        _mcq("Web security", ["sql"], "medium", "What is the standard defence against SQL injection?", ["Hiding the database name", "Parameterised queries (prepared statements)", "Using longer table names", "Disabling HTTPS"], 1, "Parameters keep user input separate from SQL code."),
        _mcq("JavaScript", ["javascript"], "hard", "In JavaScript, when does a setTimeout(fn, 0) callback run?", ["Immediately, before the current code", "After the current call stack has finished", "Never", "Only after a page reload"], 1, "The event loop runs it once the stack is empty."),
        _mcq("CSS", ["css"], "easy", "In CSS flexbox, what does justify-content control?", ["Alignment along the main axis", "Font size", "Border colour", "Image loading"], 0, "justify-content distributes items along the main axis."),
        _mcq("Authentication", ["rest api"], "hard", "Which statement about a standard signed JWT is correct?", ["Its payload is encrypted by default", "Its payload is only base64url-encoded, so anyone holding the token can read it", "It must be stored in the server database to be valid", "It cannot contain an expiry time"], 1, "A signed JWT is tamper-evident but not confidential."),
        _short("Browsers", ["javascript", "css"], "medium", "Describe what happens from typing a URL into the browser until the page is shown.", ["DNS lookup and connection (TCP/TLS)", "HTTP request and server response", "Browser parses HTML/CSS and builds the DOM/render tree", "JavaScript runs and page is painted"], "Look for the main stages in order."),
        _short("Rendering", ["react", "javascript"], "medium", "Explain the difference between client-side rendering and server-side rendering, with one advantage of each.", ["CSR renders in the browser using JavaScript, SSR renders HTML on the server", "SSR: faster first paint and better SEO", "CSR: rich interactivity, less server work after load"], "A balanced comparison is expected."),
        _short("Web security", ["rest api"], "medium", "How would you secure a login form and its API against common attacks?", ["HTTPS and secure password hashing", "Rate limiting / lockout and input validation", "CSRF and XSS protections, secure cookies or tokens"], "Look for several layers of protection."),
    ],
    "mobile": [
        _mcq("Mobile performance", ["mobile development"], "easy", "Why should long-running network calls not run on a mobile app's main (UI) thread?", ["They would use more battery", "They block UI updates and make the app freeze", "They are not allowed by the network", "They cannot return data"], 1, "The UI thread must stay free to draw and respond."),
        _mcq("Mobile security", ["mobile development"], "medium", "Where should an authentication token be stored on a mobile device?", ["In plain text inside the app code", "In the platform's secure storage (Keychain or Keystore)", "In a public folder", "In the app's screenshot cache"], 1, "Secure storage protects secrets from other apps."),
        _mcq("Mobile UX", ["mobile development"], "easy", "What is pagination (lazy loading) in a long list screen?", ["Loading all data at once", "Loading data in small pages as the user scrolls", "Sorting the list", "Deleting old items"], 1, "Loading in pages keeps screens fast and saves data."),
        _mcq("Mobile architecture", ["mobile development"], "medium", "What does an offline-first mobile app do?", ["Refuses to work without internet", "Stores data locally and syncs when a connection returns", "Only shows ads", "Downloads the whole internet"], 1, "Local storage plus later synchronisation keeps the app usable offline."),
        _mcq("Mobile platform", ["mobile development"], "easy", "What is a good practice when requesting app permissions such as location or camera?", ["Request all of them at install time", "Ask at the moment the feature needs it and explain why", "Never explain", "Request them every second"], 1, "Contextual requests build trust and increase approval."),
        _short("Mobile architecture", ["mobile development", "rest api"], "medium", "How would you design a mobile screen that shows a list from an API so it stays fast and handles poor connectivity?", ["Pagination and caching", "Loading and error/retry states", "Local storage for offline use"], "Look for performance and resilience ideas."),
    ],
    "general": [
        _mcq("Algorithms", ["algorithms"], "easy", "What is the time complexity of binary search on a sorted array of n items?", ["O(n)", "O(log n)", "O(n log n)", "O(1)"], 1, "Each step halves the search range."),
        _mcq("Data structures", ["data structures"], "easy", "Which principle does a stack follow?", ["First in, first out", "Last in, first out", "Random access only", "Sorted order"], 1, "A stack removes the most recently added item first."),
        _mcq("Data structures", ["data structures"], "medium", "What is a hash collision?", ["Two different keys mapping to the same bucket", "A key that is missing", "A table that is full", "A sorted array"], 0, "Collisions are handled by chaining or probing."),
        _mcq("Algorithms", ["algorithms"], "medium", "Which data structure does breadth-first search (BFS) typically use?", ["Stack", "Queue", "Heap only", "Binary tree only"], 1, "BFS explores level by level using a queue."),
        _mcq("Git", ["git"], "easy", "Which Git command shows changes you have not yet staged?", ["git push", "git diff", "git clone", "git remote"], 1, "git diff compares the working tree with the index."),
        _mcq("Testing", ["testing"], "easy", "What is the main purpose of a unit test?", ["To test the whole system in production", "To check that a small piece of code behaves as expected", "To measure server cost", "To design the UI"], 1, "Unit tests verify small units in isolation."),
        _mcq("Databases", ["sql"], "medium", "What is the main trade-off of adding a database index?", ["It speeds up reads but slows down writes and uses extra space", "It slows down reads", "It deletes duplicate rows", "It has no cost"], 0, "Indexes must be maintained on every write."),
        _mcq("Databases", ["sql"], "medium", "In ACID, what does Atomicity mean?", ["A transaction is all-or-nothing", "Data is always encrypted", "Queries are always fast", "Tables never change"], 0, "Either every step of a transaction is applied or none is."),
        _mcq("Algorithms", ["algorithms"], "easy", "Why does every recursive function need a base case?", ["To make it faster", "To stop the recursion instead of running forever", "To use less memory always", "To make it iterative"], 1, "Without a base case the calls never end."),
        _mcq("Data structures", ["data structures"], "easy", "Which data structure gives O(1) average-time lookup by key?", ["Hash map", "Linked list", "Sorted array scan", "Stack"], 0, "Hash maps compute the bucket from the key."),
        _short("Operating systems", ["algorithms"], "medium", "Explain the difference between a process and a thread.", ["A process has its own memory space; threads share the process memory", "Threads are lighter to create and switch", "Shared memory needs synchronisation"], "Memory isolation versus sharing is the key contrast."),
        _short("Debugging", ["testing", "git"], "medium", "A feature that worked yesterday is failing for users today. Describe how you would debug it.", ["Reproduce the problem and read logs/errors", "Check recent changes (git history, deployments, config)", "Isolate the cause, fix, add a test, verify"], "Look for a systematic approach."),
    ],
}

ROLE_FAMILIES: dict[str, list[str]] = {
    "python-developer": ["python", "general"],
    "backend-developer": ["python", "web", "general"],
    "frontend-developer": ["web", "general"],
    "full-stack-developer": ["web", "python", "general"],
    "mobile-app-developer": ["mobile", "web", "general"],
    "ai-ml-engineer-intern": ["ml", "python", "general"],
    "junior-ai-engineer": ["ml", "python", "general"],
    "data-scientist": ["data", "ml", "python"],
}


def families_for(role_slug: str) -> list[str]:
    return ROLE_FAMILIES.get(role_slug, ["general", "python"])


def fill(role_slug: str, need: int, known_prompts: list[str], seed: int) -> list[dict]:
    """Return up to `need` bank questions for this role as {'q': GenQuestion, 'category': ...}, skipping any similar to `known_prompts`.
    Roughly 70% multiple choice and 30% short answer. Deterministic for a given seed."""
    if need <= 0:
        return []
    rng = random.Random(seed)  # noqa: S311 - variety, not security
    fams = families_for(role_slug)
    pool: list[dict] = []
    for rank, fam in enumerate(fams):
        items = list(BANK.get(fam, []))
        rng.shuffle(items)
        for n, it in enumerate(items):
            pool.append({**it, "_order": n * len(fams) + rank})  # interleave families so a mixed role gets a mixed test
    pool.sort(key=lambda x: x["_order"])
    want_short = max(1, round(need * 0.3)) if need >= 4 else 0
    mcqs = [p for p in pool if p["type"] == "mcq"]
    shorts = [p for p in pool if p["type"] == "short_answer"]
    out: list[dict] = []
    seen = list(known_prompts)

    def take(items: list[dict], limit: int, category: str) -> None:
        taken = 0
        for it in items:
            if taken >= limit:
                break
            if any(validate.similar(it["prompt"], k) for k in seen):
                continue
            data = {k: v for k, v in it.items() if not k.startswith("_")}
            out.append({"q": GenQuestion(**data), "category": category})
            seen.append(it["prompt"])
            taken += 1

    take(shorts, want_short, "role_problem_solving")
    take(mcqs, need - len(out), "technical")
    if len(out) < need:
        take(shorts, need - len(out), "role_problem_solving")
    rng.shuffle(out)
    return out[:need]
