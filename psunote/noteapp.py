import flask

import models
import forms

from datetime import datetime

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    # ดึงข้อมูล tag ที่ตรงกับ tag_name
    tag = db.session.execute(
        db.select(models.Tag).where(models.Tag.name == tag_name)
    ).scalars().first()
    
    # หากไม่พบ tag ให้รีไดเร็กต์ไปที่หน้าแรก
    if not tag:
        return flask.redirect(flask.url_for("index"))
    
    # ดึง notes ที่เชื่อมโยงกับ tag นี้
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    # ส่ง tag และ notes ไปยังเทมเพลต
    return flask.render_template(
        "tags-view.html",
        tag=tag,  # ส่ง tag ไปยังเทมเพลต
        tag_name=tag_name,
        notes=notes,
    )


@app.route("/notes/edit/<int:note_id>", methods=["GET", "POST"])
def notes_edit(note_id):
    db = models.db
    note = db.session.get(models.Note, note_id)
    if not note:
        return flask.redirect(flask.url_for("index"))

    form = forms.NoteForm(obj=note)
    if form.validate_on_submit():
        note.title = form.title.data
        note.description = form.description.data

        note.updated_date = datetime.utcnow()

        note.tags = []

        for tag_name in form.tags.data:
            tag = (
                db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
                .scalars()
                .first()
            )

            if not tag:
                tag = models.Tag(name=tag_name)
                db.session.add(tag)

            note.tags.append(tag)

        db.session.commit()

        return flask.redirect(flask.url_for("index"))

    return flask.render_template("notes-edit.html", form=form, note=note)

@app.route("/notes/delete/<int:id>", methods=["POST"])
def notes_delete(id):
    db = models.db
    note = db.session.execute(db.select(models.Note).where(models.Note.id == id)).scalars().first()
    if note:
        db.session.delete(note)
        db.session.commit()
    return flask.redirect(flask.url_for("index"))

@app.route('/tags/edit/<int:id>', methods=['GET', 'POST'])
def tags_edit(id):
    tag = models.Tag.query.get_or_404(id)
    form = forms.TagForm(obj=tag)  # ใช้ฟอร์ม TagForm
    if form.validate_on_submit():
        tag.name = form.title.data  # อัพเดตชื่อ Tag
        models.db.session.commit()
        flask.flash('Tag updated successfully!', 'success')
        return flask.redirect(flask.url_for('tags_view', tag_name=tag.name))
    return flask.render_template('tags-edit.html', form=form, tag=tag)



@app.route('/tags/delete/<int:id>', methods=['POST'])
def tags_delete(id):
    # Fetch the tag using the given id, or return a 404 error if not found
    tag = models.Tag.query.get_or_404(id)
    
    # Check if tag has associated notes
    if tag.notes:
        # Clear the relationship between the tag and notes
        tag.notes.clear()  # This removes all references to this tag in the notes
        
        # Commit the changes to remove the relationship
        models.db.session.commit()

    # Now delete the tag itself
    models.db.session.delete(tag)
    models.db.session.commit()

    # Flash a success message
    flask.flash("Tag deleted successfully")
    
    # Redirect to the 'home' page instead of 'tags_view'
    return flask.redirect(flask.url_for("index"))






if __name__ == "__main__":
    app.run(debug=True)
