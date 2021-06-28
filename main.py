from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fpso_db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
myDb = SQLAlchemy(app)
ma = Marshmallow(app)

class Vessel(myDb.Model):
    id = myDb.Column(myDb.Integer, primary_key=True)
    code = myDb.Column(myDb.String(5), unique=True, nullable=False)
    equipments = myDb.relationship('Equipment', backref='vessel')

    def __init__(self, code):
        self.code = code

class Equipment(myDb.Model):
    id = myDb.Column(myDb.Integer, primary_key=True)
    name = myDb.Column(myDb.String(12), nullable=False)
    code = myDb.Column(myDb.String(8), unique=True, nullable=False)
    location = myDb.Column(myDb.String(3), nullable=False)
    status = myDb.Column(myDb.String(12), nullable=False)
    vesselCode = myDb.Column(myDb.String(5), myDb.ForeignKey('vessel.code'))

    def __init__(self, name, code, location, status, vesselCode='active'):
        self.name = name
        self.code = code
        self.location = location
        self.status = status
        self.vesselCode = vesselCode

class VesselSchema(ma.Schema):
    class Meta: 
        fields = ('id', 'code')

class EquipmentSchema(ma.Schema):
    class Meta: 
        fields = ('id', 'name', 'code', 'location', 'status', 'vesselCode')

myVesselSchema = VesselSchema()
myVesselsSchema = VesselSchema(many=True)

myEquipSchema = EquipmentSchema()
myEquipsSchema = EquipmentSchema(many=True)

@app.route('/api/vessels/post', methods=['POST'])
def add_vessel():
    code = request.json['code']
    try:
        newVessel = Vessel(code)
        myDb.session.add(newVessel)
        myDb.session.commit()
    except IntegrityError:
        myDb.session.rollback()
        return jsonify({'Message': f'Vessel {code} already exists.'}), 409
    
    return jsonify({'Message': f'Vessel {code} inserted.'}), 201

@app.route('/api/equips/post', methods=['POST'])
def add_equip():
    name = request.json['name']
    code = request.json['code']
    location = request.json['location']
    status = request.json['status']
    vesselCode = request.json['vesselCode']
    try:
        newEquip = Equipment(name, code, location, status, vesselCode)
        myDb.session.add(newEquip)
        myDb.session.commit()
    except IntegrityError:
        myDb.session.rollback()
        return jsonify({'Message': f'Equipment {code} already exists.'}), 409
        
    return jsonify({'Message': f'Equipment {code} inserted.'}), 201

@app.route('/api/vessels/get', methods=['GET'])
def get_vessels():
    allVessels = Vessel.query.all()
    result = myVesselsSchema.dump(allVessels)
    return jsonify(result)

@app.route('/api/equips/get', methods=['GET'])
def get_equips():
    allEquips = Equipment.query.all()
    result = myEquipsSchema.dump(allEquips)
    return jsonify(result)

@app.route('/api/equips/get/<status>', methods=['GET'])
def get_equips_status(status):
    allEquips = Equipment.query.filter_by(status = status).all()
    result = myEquipsSchema.dump(allEquips)
    return jsonify(result), 200

@app.route('/api/vessels/get/<id>', methods=['GET'])
def get_a_vessel(id):
    myVessel = Vessel.query.get(id)
    return myVesselSchema.jsonify(myVessel), 200

@app.route('/api/vessels/update/code/<id>', methods=['PUT'])
def update_a_vessel(id):
    myVessel = Vessel.query.get(id)

    code = request.json['code']
    myVessel.code = code

    myDb.session.commit()
    return myVesselSchema.jsonify(myVessel), 200

@app.route('/api/equips/update/status/<code>', methods=['PUT'])
def update_a_equip_status(code):
    myEquip = Equipment.query.filter_by(code = code).first()
    myEquip.status = 'inactive'
    myDb.session.commit()
    return myEquipSchema.jsonify(myEquip), 200

@app.route('/api/equips/update/status_all', methods=['PUT'])
def update_list_equip_status():
        myList = request.json
        myEquips = Equipment.query.filter(Equipment.code.in_(myList)).all()
        for equip in myEquips:
            equip.status = 'inactive'
        myDb.session.commit()
        result = myEquipsSchema.dump(myEquips)
        return jsonify(result), 200

@app.route('/api/vessels/delete/<id>', methods=['DELETE'])
def delete_a_vessel(id):
    myVessel = Vessel.query.get(id)

    myDb.session.delete(myVessel)
    myDb.session.commit()

    return myVesselSchema.jsonify(myVessel),200

if __name__ == '__main__':
    myDb.create_all()
    app.run(debug=True)