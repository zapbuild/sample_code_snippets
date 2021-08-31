using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using SautinSoft.Document;
using SautinSoft.Document.Drawing;
using System.Configuration;
using log4net;
using BarrelApp.App_Code.Helper;
using BarrelApp.Models;
namespace BarrelApp.App_Code
{
    //
    // Summary:
    //     this class is to create document of certificate of title
    public class CertificateOfTitleDocument : TemplateDocument
    {
        //
        // Summary:
        //      Member variable for class instance
        private static CertificateOfTitleDocument _instance;
        // Summary:
        //      get and set the instance of CertificateOfTitleDocument class
        // Return:
        //      Instance of CertificateOfTitleDocument class
        public static CertificateOfTitleDocument Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = new CertificateOfTitleDocument();
                }
                return _instance;
            }
        }
        // Summary:
        //      Create certificate of title document
        // Parameters:
        //      templatePath: template base/sample path of document
        //      mappings: all case details fields mapping list that will mapp in the document
        //      liens: liens listing that will attach in the document
        // Return:
        //      combined object of DocumentCore for final certificate of title docx document
        public DocumentCore Create(string templatePath, List<vwTemplateMapping> mappings, List<vwLien> liens)
        {
            vwLien lienFeeSimple = liens.FirstOrDefault(rec => rec.InstrumentType == "Fee Simple");

            List<string> missingData = new List<string>();
            if (liens.Count == 0)
                missingData.Add("Liens");
            if (lienFeeSimple == null)
                missingData.Add("Fee Simple");

            if (missingData.Count > 0)
            {
                throw new ApplicationException(string.Join(",", missingData));
            }

            List<DocumentCore> documents = new List<DocumentCore>();

            documents.Add(DocumentCore.Load(templatePath));

            documents.Add(createEXHIBITA());

            documents.Add(createEXHIBITB(liens));

            DocumentCore dcSingle = combinedDocument(documents);

            Utility.ReplacePlaceHolders(mappings, dcSingle);
            return dcSingle;
        }

        // Summary:
        //      Create Exhibit A section in the document and add legal description placeholder
        // Return:
        //      object of DocumentCore
        private DocumentCore createEXHIBITA()
        {
            return createTitlePage("EXHIBIT A", Convert.ToDouble(12f), null, null, 0, "LEGALDESC");
        }
        // Summary:
        //      Create Exhibit B section in the document
        //      Attach the liens in the exhibit B
        // Return:
        //      object of DocumentCore
        private DocumentCore createEXHIBITB(List<vwLien> liens)
        {
            DocumentCore exhibitDoc = createTitlePage("EXHIBIT B", Convert.ToDouble(12f), "Liens", Convert.ToDouble(10f), 0, null);

            for (int i = 0; i < 2; i++)
            {
                exhibitDoc.Sections.Last().Content.End.Insert("\n");
            }

            ListStyle ordList = new ListStyle("Simple Numbers", ListTemplateType.NumberWithDot);
            foreach (ListLevelFormat f in ordList.ListLevelFormats)
            {
                f.CharacterFormat.Size = 12;
                f.CharacterFormat.FontName = "Times New Roman";
            }
            exhibitDoc.Styles.Add(ordList);

            int level = 0;
            foreach (vwLien lien in liens.Where(rec => rec.InstrumentType != "Fee Simple"))
            {
                Paragraph p = null;
                string text = lien.InstrumentDescription;
                if (text != null && text != "")
                {
                    string[] tokens = text.Split('\n');
                    for (int i = 0; i < tokens.Length; i++)
                    {
                        p = new Paragraph(exhibitDoc);
                        p.Content.End.Insert(tokens[i],
                            new CharacterFormat() { FontName = "Times New Roman", Size = 12.0, FontColor = Color.Black });
                        p.ListFormat.Style = ordList;
                        p.ListFormat.ListLevelNumber = level;
                        p.ParagraphFormat.SpaceAfter = 0;
                        p.ParagraphFormat.LineSpacing = 1.00;
                        p.ParagraphFormat.LineSpacingRule = LineSpacingRule.Multiple;
                        exhibitDoc.Sections.Last().Content.End.Insert(p.Content);
                    }
                }
            }

            return exhibitDoc;
        }

    }
}