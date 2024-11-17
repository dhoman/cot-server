# Poor man's Chain of Thought Server

I wanted to have chain of thought capabilities similar to o1, but be unrestricted by api limits, and hopefully be able to leverage 4o's web search and other tooling.

This is my first stab at it.

## next steps
I think the system messages could be improved and that I could have it follow a schema (function calling) to have the model generate <thought> tags to improve the quality, but this is good enough for me for right now. (Scratched the itch at the moment).
I'd also like to improve the logging.

## run server
in wsl  
`python3 app.py`
## hit server
in wsl
`python3 test.py`
