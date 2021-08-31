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
    //        TemplateDocument is parent class for template document and this is being
    //        extends by all template document i,e Petition/Summon/ProcessServer/
    //        CertificateOfTitle and others
    //        This class is created to use the SautinSoft common features
    public class TemplateDocument
    {
        // Summary:
        //      contructor of TemplateDocument
        //      set the license key of SautinSoft
        private TemplateDocument()
        {
            DocumentCore.Serial = ConfigurationManager.AppSettings["SautinSoftDocumentNetKey"].ToString();
        }
        //
        // Summary:
        //        Create exhibit section in the document
        // Parameters:
        //        title: exhibit Name
        //        size:  exhibit Name font size
        //        subTitle: exhibit sub heading
        //        subTitleSize: exhibit sub heading font size
        //        docs: documents that will attach in this exhibit
        //        topBlank: space between exhibit heading and documents
        //        placeHolder: if want to add some placeholder in this exhibit that will
        //        map by case details
        // Return:
        //      return the object of DocumentCore that will combined in single docx document
        protected DocumentCore createEXHIBIT(string title, double? size, string subTitle, double? subTitleSize,
            List<DocumentCore> docs, int? topBlank, string placeHolder)
        {
            DocumentCore dc = new DocumentCore();
            dc.DefaultParagraphFormat.SpaceAfter = 1.0;
            ImportSession session;
            Section importedSection;

            if (docs == null)
                docs = new List<DocumentCore>();

            if (title != null)
                docs.Insert(0, createTitlePage(title, Convert.ToDouble(size), subTitle, subTitleSize, topBlank, placeHolder));

            foreach (DocumentCore doc in docs)
            {
                session = new ImportSession(doc, dc, StyleImportingMode.KeepSourceFormatting);
                foreach (Section sourceSection in doc.Sections)
                {
                    importedSection = dc.Import<Section>(sourceSection, true, session);
                    importedSection.PageSetup.PaperType = PaperType.Letter;
                    importedSection.PageSetup.Orientation = Orientation.Portrait;

                    if (doc.Sections.IndexOf(sourceSection) == 0)
                        importedSection.PageSetup.SectionStart = SectionStart.NewPage;

                    dc.Sections.Add(importedSection);
                }
            }

            return dc;
        }
        //
        // Summary:
        //        Create exhibit heading and sub heading
        // Parameters:
        //        title: exhibit Name
        //        size:  exhibit Name font size
        //        subTitle: exhibit sub heading
        //        subTitleSize: exhibit sub heading font size
        //        topBlank: space between exhibit heading and documents
        //        placeHolder: if want to add some placeholder in this exhibit that will
        //        map by case details
        // Return:
        //      return the object of DocumentCore that will combined in single docx document
        protected DocumentCore createTitlePage(string title, double size, string subTitle, double? subTitleSize,
            int? topBlank, string placeHolder)
        {
            topBlank = topBlank == null ? 12 : topBlank;

            DocumentCore dc = new DocumentCore();
            Section s = new Section(dc);
            s.PageSetup.PaperType = PaperType.Letter;
            s.PageSetup.Orientation = Orientation.Portrait;
            dc.Sections.Add(s);

            for (int i = 0; i < topBlank; i++)
            {
                s.Content.Start.Insert("\n");
            }

            // Add a paragraph.
            Paragraph p = new Paragraph(dc);
            p.ParagraphFormat.Alignment = HorizontalAlignment.Center;
            s.Blocks.Add(p);
            p = SautinSoftDocumentHelper.Instance.InsertStringToParagraph(p, dc, title, size, false, true);

            if (subTitle != null)
            {
                p = new Paragraph(dc);
                p.ParagraphFormat.Alignment = HorizontalAlignment.Center;
                s.Blocks.Add(p);
                p = SautinSoftDocumentHelper.Instance.InsertStringToParagraph(p, dc, subTitle, size, false, false);
            }

            if (placeHolder != null)
            {
                p = new Paragraph(dc);
                p.ParagraphFormat.Alignment = HorizontalAlignment.Left;
                s.Blocks.Add(p);
                p = SautinSoftDocumentHelper.Instance.InsertStringToParagraph(p, dc, "<<" + placeHolder + ">>", size, false, false);
            }

            return dc;
        }

        //
        // Summary:
        //        Create Attach document in the document that will combined in single
        // Parameters:
        //        docType: document type pdf/image/docx
        //        docData:  document bytes
        // Return:
        //      return the object of DocumentCore that will combined in single docx document
        protected DocumentCore createDocument(string docType, byte[] docData)
        {
            using (MemoryStream msInp = new MemoryStream(docData))
            {
                if (docType == "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    return DocumentCore.Load(msInp, LoadOptions.DocxDefault);
                else if (docType == "application/pdf")
                {
                    return MappingHelper.Instance.PDFToImages(docData);
                }
                else if (docType == "image/jpeg" || docType == "image/jpg" || docType == "image/png")
                {
                    PictureFormat pf = PictureFormat.Unknown;
                    if (docType == "image/jpeg" || docType == "image/jpg")
                        pf = PictureFormat.Jpeg;
                    else if (docType == "image/png")
                        pf = PictureFormat.Png;

                    Picture pic = new Picture(dcInstance, msInp, pf);
                    pic.Layout.Size = new Size(470, 680);
                    dcInstance.Content.End.Insert(pic.Content);
                    return dcInstance;
                }
                else
                    throw new ApplicationException("Create Document Type " + docType + " not supported");
            }
        }
        //
        // Summary:
        //        Combined all assemble documents into one single
        // Parameters:
        //        documents: list of DocumentCore objects
        // Return:
        //      return the object of DocumentCore
        protected DocumentCore combinedDocument(List<DocumentCore> documents)
        {

            DocumentCore dcSingle = new DocumentCore();
            dcSingle.DefaultParagraphFormat.SpaceAfter = 1.0;
            dcSingle.DefaultCharacterFormat.FontName = "Times New Roman";
            dcSingle.DefaultCharacterFormat.Size = 12f;

            foreach (DocumentCore dc in documents)
            {
                ImportSession session = new ImportSession(dc, dcSingle, StyleImportingMode.KeepSourceFormatting);
                foreach (Section sourceSection in dc.Sections)
                {
                    Section importedSection = dcSingle.Import<Section>(sourceSection, true, session);

                    if (dc.Sections.IndexOf(sourceSection) == 0)
                        importedSection.PageSetup.SectionStart = SectionStart.NewPage;


                    dcSingle.Sections.Add(importedSection);
                }
            }
            return dcSingle;
        }

    }
}