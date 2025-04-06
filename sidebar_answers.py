import streamlit as st
import json

# Load the JSON data (ensure the french_json_data variable contains the actual JSON string or load it from a file)
# For demonstration, the JSON data from the previous step is included as a multiline string.
# In a real application, you might load this from a file or another source.
french_json_data_string = """
[
  {
    "question": "Montrez des images liées au conseil administratif de l'Association France-Canada vers 1978-1980.",
    "ground_truth": [
      {
        "ID": "E5",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00005.jpg",
        "content": "Association France-Canada, conseil administratif",
        "year": "1978-1980",
        "locality": "Acadie"
      },
      {
        "ID": "E6",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00006.jpg",
        "content": "Association France-Canada, conseil administratif",
        "year": "1978-1980",
        "locality": "Acadie"
      }
    ]
  },
  {
    "question": "Trouvez des photos montrant des présentations de cadeaux par l'Association France-Canada en 1976.",
    "ground_truth": [
      {
        "ID": "E12",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00012.jpg",
        "content": "Association France-Canada, présentation - cadeau",
        "year": "1976",
        "locality": "Acadie"
      },
      {
        "ID": "E13",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00013.jpg",
        "content": "Association France-Canada, présentation - cadeau",
        "year": "1976",
        "locality": "Acadie"
      }
    ]
  },
  {
    "question": "Montrez-moi des images liées aux présentations de livres par l'Association France-Canada entre 1976 et 1982.",
    "ground_truth": [
      {
        "ID": "E14",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00014.jpg",
        "content": "Association France-Canada, présentation - livre",
        "year": "1976-1982",
        "locality": "Acadie"
      },
      {
        "ID": "E15",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00015.jpg",
        "content": "Association France-Canada, présentation - livre",
        "year": "1976-1982",
        "locality": "Acadie"
      }
    ]
  },
  {
    "question": "Pouvez-vous trouver des photos illustrant des réceptions tenues par l'Association France-Canada en 1980 ?",
    "ground_truth": [
      {
        "ID": "E17",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00017.jpg",
        "content": "Association France-Canada, réception",
        "year": "1980",
        "locality": "Acadie"
      },
      {
        "ID": "E18",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00018.jpg",
        "content": "Association France-Canada, réception",
        "year": "1980",
        "locality": "Acadie"
      },
      {
        "ID": "E19",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00019.jpg",
        "content": "Association France-Canada, réception",
        "year": "1980",
        "locality": "Acadie"
      }
    ]
  },
  {
    "question": "Récupérez des images montrant les activités de voyage de l'Association France-Canada de 1978-1979.",
    "ground_truth": [
      {
        "ID": "E26",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00026.jpg",
        "content": "Association France-Canada, voyage",
        "year": "1978-1979",
        "locality": "Acadie"
      },
      {
        "ID": "E27",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00027.jpg",
        "content": "Association France-Canada, voyage",
        "year": "1978-1979",
        "locality": "Acadie"
      },
       {
        "ID": "E28",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00028.jpg",
        "content": "Association France-Canada, voyage",
        "year": "1978-1979",
        "locality": "Acadie"
      }
    ]
  },
  {
    "question": "Trouvez des photos des délégués de la Biennale en Acadie en 1977.",
    "ground_truth": [
       {
        "ID": "E32",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00032.jpg",
        "content": "Biennale, délégués",
        "year": "1977",
        "locality": "Acadie"
      },
       {
        "ID": "E33",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00033.jpg",
        "content": "Biennale, délégués",
        "year": "1977",
        "locality": "Acadie"
      }
    ]
  },
  {
    "question": "Montrez des images de la conférence internationale de 1980 sur les communautés ethniques de langue française tenue en Acadie.",
    "ground_truth": [
      {
        "ID": "E35",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00035.jpg",
        "content": "Communautés ethniques de langue française, conférence internationale",
        "year": "1980",
        "locality": "Acadie"
      },
       {
        "ID": "E36",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00036.jpg",
        "content": "Communautés ethniques de langue française, conférence internationale",
        "year": "1980",
        "locality": "Acadie"
      }
    ]
  },
  {
    "question": "Y a-t-il des photos des conférences de presse de la FFHQ datant de 1979 ?",
    "ground_truth": [
      {
        "ID": "E45",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00045.jpg",
        "content": "FFHQ-Fédération des Francophones Hors-Québec, conférence de presse",
        "year": "1979",
        "locality": "Acadie"
      },
       {
        "ID": "E46",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00046.jpg",
        "content": "FFHQ-Fédération des Francophones Hors-Québec, conférence de presse",
        "year": "1979",
        "locality": "Acadie"
      }
    ]
  },
   {
    "question": "Trouvez des images liées au colloque de la Société Nationale des Acadiens (SNA) en 1982.",
    "ground_truth": [
       {
        "ID": "E54",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00054.jpg",
        "content": "SNA-Société Nationale des Acadiens, colloque",
        "year": "1982",
        "locality": "Acadie"
      },
      {
        "ID": "E55",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00055.jpg",
        "content": "SNA-Société Nationale des Acadiens, colloque",
        "year": "1982",
        "locality": "Acadie"
      }
    ]
  },
   {
    "question": "Montrez des photos non datées du conseil administratif de la SNA.",
    "ground_truth": [
       {
        "ID": "E57",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00057.jpg",
        "content": "SNA-Société Nationale des Acadiens, conseil administratif",
        "year": "s.d.",
        "locality": "Acadie"
      },
      {
        "ID": "E58",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00058.jpg",
        "content": "SNA-Société Nationale des Acadiens, conseil administratif",
        "year": "s.d.",
        "locality": "Acadie"
      }
    ]
  },
  {
    "question": "Trouvez des photos des réunions annuelles de la SNA en 1971.",
    "ground_truth": [
      {
        "ID": "E65",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00065.jpg",
        "content": "SNA-Société Nationale des Acadiens, réunion annuelle",
        "year": "1971",
        "locality": "Acadie"
      },
      {
        "ID": "E66",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00066.jpg",
        "content": "SNA-Société Nationale des Acadiens, réunion annuelle",
        "year": "1971",
        "locality": "Acadie"
      }
    ]
  },
   {
    "question": "Montrez des images non datées liées aux présentations SNA/SONA.",
    "ground_truth": [
       {
        "ID": "E67",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00067.jpg",
        "content": "SNA-Société Nationale des Acadiens, SONA - présentation",
        "year": "s.d.",
        "locality": "Acadie"
      },
      {
        "ID": "E68",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00068.jpg",
        "content": "SNA-Société Nationale des Acadiens, SONA - présentation",
        "year": "s.d.",
        "locality": "Acadie"
      }
    ]
  },
   {
    "question": "Trouvez des photos de l'exécutif de l'Association des écrivains acadiens entre 1979-1982.",
    "ground_truth": [
       {
        "ID": "E79",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00079.jpg",
        "content": "Association des écrivains acadiens, exécutif",
        "year": "1979-1982",
        "locality": "Acadie"
      },
      {
        "ID": "E80",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00080.jpg",
        "content": "Association des écrivains acadiens, exécutif",
        "year": "1979-1982",
        "locality": "Acadie"
      }
    ]
  },
  {
    "question": "Montrez-moi des images liées à la recherche de boursières à l'Université South Western de la Louisiane en 1969.",
    "ground_truth": [
       {
        "ID": "E85",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00085.jpg",
        "content": "Université South Western de la Louisiane, recherche boursières",
        "year": "1969",
        "locality": "Acadie"
      },
      {
        "ID": "E86",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00086.jpg",
        "content": "Université South Western de la Louisiane, recherche boursières",
        "year": "1969",
        "locality": "Acadie"
      }
    ]
  },
  {
    "question": "Pouvez-vous récupérer des images montrant l'arrivée lors de la 'Visite des quatre' en 1968 ?",
    "ground_truth": [
       {
        "ID": "E98",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00098.jpg",
        "content": "Visite des quatre, arrivée",
        "year": "1968",
        "locality": "Acadie"
      },
      {
        "ID": "E99",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00099.jpg",
        "content": "Visite des quatre, arrivée",
        "year": "1968",
        "locality": "Acadie"
      }
    ]
  },
  {
    "question": "Montrez-moi des photos liées aux interviews pendant la 'Visite des quatre' en 1968.",
    "ground_truth": [
       {
        "ID": "E109",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-0109.jpg",
        "content": "Visite des quatre, interview",
        "year": "1968",
        "locality": "Acadie"
      },
      {
        "ID": "E110",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-0110.jpg",
        "content": "Visite des quatre, interview",
        "year": "1968",
        "locality": "Acadie"
      }
    ]
  },
   {
    "question": "Trouvez des images de la cueillette de bleuets à Acadieville en 1974.",
    "ground_truth": [
      {
        "ID": "E122",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00122.jpg",
        "content": "Culture, bleuets cueillette",
        "year": "1974",
        "locality": "Acadieville"
      },
      {
        "ID": "E123",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00123.jpg",
        "content": "Culture, bleuets cueillette",
        "year": "1974",
        "locality": "Acadieville"
      }
    ]
  },
   {
    "question": "Montrez des photos des activités de la caisse scolaire de la Caisse populaire à Acadieville, 1972.",
    "ground_truth": [
       {
        "ID": "E125",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00125.jpg",
        "content": "Caisse populaire, caisse scolaire",
        "year": "1972",
        "locality": "Acadieville"
      },
       {
        "ID": "E126",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00126.jpg",
        "content": "Caisse populaire, caisse scolaire",
        "year": "1972",
        "locality": "Acadieville"
      }
    ]
  },
   {
    "question": "Récupérez des photos montrant des présentations de plaques par la Caisse populaire à Acadieville entre 1972-1978.",
    "ground_truth": [
       {
        "ID": "E130",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00130.jpg",
        "content": "Caisse populaire, présentation plaque",
        "year": "1972-1978",
        "locality": "Acadieville"
      },
      {
        "ID": "E131",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00131.jpg",
        "content": "Caisse populaire, présentation plaque",
        "year": "1972-1978",
        "locality": "Acadieville"
      }
    ]
  },
  {
    "question": "Pouvez-vous trouver des photos liées à la cérémonie d'anniversaire de la paroisse à Acadieville en 1971 ?",
    "ground_truth": [
       {
        "ID": "E142",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00142.jpg",
        "content": "Anniversaire de paroisse, cérémonie",
        "year": "1971",
        "locality": "Acadieville"
      },
      {
        "ID": "E143",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00143.jpg",
        "content": "Anniversaire de paroisse, cérémonie",
        "year": "1971",
        "locality": "Acadieville"
      },
      {
        "ID": "E144",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00144.jpg",
        "content": "Anniversaire de paroisse, cérémonie",
        "year": "1971",
        "locality": "Acadieville"
      }
    ]
  },
    {
    "question": "Montrez des images non datées de l'extérieur du couvent à Acadieville.",
    "ground_truth": [
      {
        "ID": "E145",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00145.jpg",
        "content": "Couvent, extérieur",
        "year": "s.d.",
        "locality": "Acadieville"
      },
      {
        "ID": "E146",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00146.jpg",
        "content": "Couvent, extérieur",
        "year": "s.d.",
        "locality": "Acadieville"
      }
    ]
  },
  {
    "question": "Trouvez des photos non datées de l'extérieur du presbytère à Acadieville.",
    "ground_truth": [
       {
        "ID": "E148",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00148.jpg",
        "content": "Presbytère, extérieur",
        "year": "s.d.",
        "locality": "Acadieville"
      },
      {
        "ID": "E149",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00149.jpg",
        "content": "Presbytère, extérieur",
        "year": "s.d.",
        "locality": "Acadieville"
      },
      {
        "ID": "E150",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00150.jpg",
        "content": "Presbytère, extérieur",
        "year": "s.d.",
        "locality": "Acadieville"
      }
    ]
  },
    {
    "question": "Montrez-moi des photos liées aux célébrations d'anniversaire ou de naissance à Acadieville vers 1977-1978.",
    "ground_truth": [
      {
        "ID": "E151",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00151.jpg",
        "content": "Anniversiare, naissance",
        "year": "1977-1978",
        "locality": "Acadieville"
      },
      {
        "ID": "E152",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00152.jpg",
        "content": "Anniversiare, naissance",
        "year": "1977-1978",
        "locality": "Acadieville"
      }
    ]
  },
  {
    "question": "Récupérez les images du comité des activités printanières à Acadieville, 1978.",
    "ground_truth": [
      {
        "ID": "E158",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00158.jpg",
        "content": "Activités printanières, comité",
        "year": "1978",
        "locality": "Acadieville"
      },
      {
        "ID": "E159",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00159.jpg",
        "content": "Activités printanières, comité",
        "year": "1978",
        "locality": "Acadieville"
      }
    ]
  },
  {
    "question": "Trouvez des photos du pageant du carnaval d'Acadieville tenu entre 1975 et 1982.",
    "ground_truth": [
      {
        "ID": "E162",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00162.jpg",
        "content": "Carnaval, pageant",
        "year": "1975-1982",
        "locality": "Acadieville"
      },
       {
        "ID": "E163",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00163.jpg",
        "content": "Carnaval, pageant",
        "year": "1975-1982",
        "locality": "Acadieville"
      }
    ]
  },
   {
    "question": "Montrez des vues extérieures du centre communautaire à Acadieville datant de 1976.",
    "ground_truth": [
      {
        "ID": "E172",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00172.jpg",
        "content": "Centre communautaire, extérieur",
        "year": "1976",
        "locality": "Acadieville"
      },
       {
        "ID": "E173",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00173.jpg",
        "content": "Centre communautaire, extérieur",
        "year": "1976",
        "locality": "Acadieville"
      }
    ]
  },
   {
    "question": "Trouvez des photos de l'intérieur du centre communautaire d'Acadieville datant de 1976.",
    "ground_truth": [
       {
        "ID": "E175",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00175.jpg",
        "content": "Centre communautaire, intérieur",
        "year": "1976",
        "locality": "Acadieville"
      },
      {
        "ID": "E176",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00176.jpg",
        "content": "Centre communautaire, intérieur",
        "year": "1976",
        "locality": "Acadieville"
      }
    ]
  },
   {
    "question": "Récupérez des images illustrant les concours lors du Festival des bleuets à Acadieville, 1977.",
    "ground_truth": [
      {
        "ID": "E181",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00181.jpg",
        "content": "Festival des bleuets, concours",
        "year": "1977",
        "locality": "Acadieville"
      },
       {
        "ID": "E182",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00182.jpg",
        "content": "Festival des bleuets, concours",
        "year": "1977",
        "locality": "Acadieville"
      },
       {
        "ID": "E183",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00183.jpg",
        "content": "Festival des bleuets, concours",
        "year": "1977",
        "locality": "Acadieville"
      }
    ]
  },
  {
    "question": "Montrez des photos liées au pageant du Festival des bleuets à Acadieville entre 1977 et 1980.",
    "ground_truth": [
       {
        "ID": "E184",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00184.jpg",
        "content": "Festival des bleuets, pageant",
        "year": "1977-1980",
        "locality": "Acadieville"
      },
      {
        "ID": "E185",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00185.jpg",
        "content": "Festival des bleuets, pageant",
        "year": "1977-1980",
        "locality": "Acadieville"
      }
    ]
  },
   {
    "question": "Pouvez-vous trouver des photos de l'invasion de chenilles à Adamsville en 1981 ?",
    "ground_truth": [
       {
        "ID": "E190",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00190.jpg",
        "content": "Insecte, invasion de chenilles",
        "year": "1981",
        "locality": "Adamsville"
      },
       {
        "ID": "E191",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00191.jpg",
        "content": "Insecte, invasion de chenilles",
        "year": "1981",
        "locality": "Adamsville"
      }
    ]
  },
  {
    "question": "Montrez des images liées aux mariages ou anniversaires à Adamsville entre 1976-1980.",
    "ground_truth": [
       {
        "ID": "E192",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00192.jpg",
        "content": "Anniversaire, mariage",
        "year": "1976-1980",
        "locality": "Adamsville"
      },
       {
        "ID": "E193",
        "cloud_link": "https://pub-740e51598e1f42819ec53c13af8c4f0b.r2.dev/images/E-00193.jpg",
        "content": "Anniversaire, mariage",
        "year": "1976-1980",
        "locality": "Adamsville"
      }
    ]
  }
]
"""

data = json.loads(french_json_data_string)

def show_questions_sidebar():
    """
    Displays questions and ground truth data in the Streamlit sidebar,
    hidden within an expander.

    Args:
        data (list): A list of dictionaries, where each dictionary
                     contains 'question' and 'ground_truth' keys.
                     The 'ground_truth' is a list of image details.
    """
    with st.sidebar.expander("Questions et Réponses", expanded=False):
        if not data:
            st.write("Aucune donnée de question à afficher.")
            return

        for i, item in enumerate(data):
            st.subheader(f"Question {i+1}:")
            st.write(item.get("question", "Question non disponible"))

            st.markdown("**Réponse(s) Attendue(s):**")
            ground_truths = item.get("ground_truth", [])
            if not ground_truths:
                st.caption("Aucune image de référence trouvée.")
            else:
                for gt in ground_truths:
                    gt_details = f"""
                    - **ID:** {gt.get('ID', 'N/A')}
                    - **Contenu:** {gt.get('content', 'N/A')}
                    - **Année:** {gt.get('year', 'N/A')}
                    - **Localité:** {gt.get('locality', 'N/A')}
                    - **Lien:** [link]({gt.get('cloud_link', '#')})
                    """
                    st.markdown(gt_details, unsafe_allow_html=True)
            st.divider() # Add a visual separator between questions

# Example of how to call the function in your Streamlit app:
# show_questions_sidebar(french_data)

# To run this:
# 1. Save the code as a Python file (e.g., `app.py`).
# 2. Make sure you have streamlit installed (`pip install streamlit`).
# 3. Run `streamlit run app.py` in your terminal.
# 4. Check the sidebar in the browser window that opens. Click the expander.