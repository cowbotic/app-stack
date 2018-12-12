import json

pt_data=open('PeriodicTable.json').read()

pt=json.loads(pt_data)

with open('TablaPeriodica.json', 'w') as file:
    file.write('{\n')
    for elemento in pt['elements']:
        line='"'+elemento['name']+'":{"name":"'+elemento['name']+'","symbol":"'+elemento['symbol']+'","atomic_mass":"'+str(elemento["atomic_mass"])+'","category":"'+elemento["category"]+'","density":"'+str(elemento["density"])+'","molar_heat":"'+str(elemento["molar_heat"])+'","number":"'+str(elemento["number"])+'","period":"'+str(elemento["period"])+'","source":"'+elemento["source"]+'"},'+"\n"
        print(line)
        file.write(line)
    
    file.write('}')
    file.close()



#Spectrum http://chemistry.bd.psu.edu/jircitano/Cl.gif