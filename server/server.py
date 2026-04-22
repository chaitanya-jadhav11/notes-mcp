import sys

from mcp.server.fastmcp import FastMCP, Context

from db import init_db, create_note, search_notes, list_notes, get_notes_by_title, get_note_by_id, update_note, \
    delete_note_by_id, delete_notes_by_title

# Initialize DB
init_db()
mcp = FastMCP("Notes_MCP", log_level="DEBUG")


@mcp.tool(name= "list_notes", description="List all notes")
def list_notes_tool(ctx: Context):
    """List all notes"""
    ctx.info("calling list_notes_tool :")
    print("Calling notes list:", file=sys.stderr)
    #return "list of notes: \n- note1\n- note2\n- note3"
    return list_notes()

@mcp.tool(name="create_note", description="Create a new note with title and body")
def create_note_tool(title: str, body: str):
    """Create a new note"""
    return create_note(title, body)

@mcp.tool(name="search_notes", description="Search notes")
def search_notes_tool(query: str):
    """Search notes by keyword"""
    return search_notes(query)

@mcp.tool(name="get_notes_by_title",description="Get notes by title (exact or partial match)")
def get_notes_by_title_tool(title: str, exact: bool = False):
    """Fetch notes using title"""
    return get_notes_by_title(title, exact)


@mcp.tool(name="get_note_by_id",description="Retrieve a single note using its unique ID")
def get_note_by_id_tool(note_id: str):
    """Get note by ID"""
    return get_note_by_id(note_id)

@mcp.tool( name="update_note", description="Update note title and/or body using note ID")
def update_note_tool(note_id: str, title: str = None, body: str = None):
    """Update note fields"""
    return update_note(note_id, title, body)

@mcp.tool(name="delete_note_by_id", description="Delete a note using its ID")
def delete_note_by_id_tool(note_id: str):
    """Delete note by ID"""
    return delete_note_by_id(note_id)

@mcp.tool( name="delete_notes_by_title", description="Delete all notes matching a given title")
def delete_notes_by_title_tool(title: str):
    """Delete notes by title"""
    return delete_notes_by_title(title)



# uv run mcp dev server/server.py
if __name__ == "__main__":
    print("mac server starting...")
    mcp.run(transport="stdio")

